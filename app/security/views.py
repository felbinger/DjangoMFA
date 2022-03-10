import json
from base64 import b32encode, b64encode, b64decode

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from fido2 import cbor
from fido2.client import ClientData
from fido2.ctap2 import AttestedCredentialData, AuthenticatorData, AttestationObject
from fido2.utils import websafe_decode, websafe_encode

from os import urandom
from onetimepass import valid_totp

from security.models import MfaKey, get_type


class Security(View):
    @method_decorator(login_required)
    def get(self, request: HttpRequest, *args, **kwargs):
        mfa_keys = MfaKey.objects.filter(user=request.user).exclude(state=MfaKey.MFA_STATE_SETUP).all()
        if request.headers.get("Content-Type", 'text/plain') == 'application/json':
            return HttpResponse(json.dumps({
                "mfaKeys": [
                    {
                        "uuid": str(mfa.uuid),
                        "isEnabled": mfa.is_enabled,
                        "type": mfa.type_name,
                        "description": mfa.description,
                        "dateAdded": mfa.added_on.isoformat() if mfa.added_on else None,
                        "lastUsed": mfa.last_used.isoformat() if mfa.last_used else None,
                    } for mfa in mfa_keys
                ],
            }), status=200)
        else:
            return render(request, 'security.html', context={
                "mfa_keys": mfa_keys,
            })

    @method_decorator(login_required)
    def post(self, request: HttpRequest, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        if 'type' not in data:
            return HttpResponse(status=400)

        if data.get('type').lower() == 'totp':
            mfa = MfaKey(
                user=request.user,
                type=get_type('totp'),
                mfa_data=b32encode(urandom(20)).decode('utf-8'),
                state=MfaKey.MFA_STATE_SETUP,
            )
            mfa.save()
            return HttpResponse(json.dumps({
                "uuid": str(mfa.uuid),
                "totpSecret": mfa.mfa_data,
                "username": request.user.username,
                "issuer": "DjangoMFA".replace(" ", ""),
            }), status=200)
        elif data.get('type').lower() == 'fido2':
            registration_data, request.session['state'] = settings.FIDO2_SERVER.register_begin(
                {
                    "id": request.user.id,
                    "name": request.user.username,
                    "displayName": f'{request.user.first_name} {request.user.last_name}',
                },
                user_verification="discouraged",
                authenticator_attachment="cross-platform",
            )
            mfa = MfaKey(
                user=request.user,
                type=get_type('fido2'),
                state=MfaKey.MFA_STATE_SETUP,
            )
            mfa.save()
            return HttpResponse(json.dumps({
                "uuid": str(mfa.uuid),
                "fido2Data": b64encode(cbor.encode(registration_data)).decode(),
            }), status=200)
        else:
            return HttpResponse(status=400)

    @method_decorator(login_required)
    def put(self, request: HttpRequest, uuid, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        # get the mfa key object by the uuid
        mfa = MfaKey.objects.filter(uuid=uuid).first()
        if not mfa:
            return HttpResponse(status=500)

        # in setup state, the confirmation process is being implemented
        if mfa.state == MfaKey.MFA_STATE_SETUP:
            if data.get('type', '') == 'totp':
                if 'token' not in data:
                    return HttpResponse(status=400)
                # for totp mfa this simply means to validate the token
                if not valid_totp(data['token'], mfa.mfa_data):
                    return HttpResponse(json.dumps({
                        "message": "Invalid TOTP Token",
                    }), status=400)
                mfa.description = data.get('description', '')
                mfa.state = MfaKey.MFA_STATE_ENABLED

            if data.get('type', '') == 'fido2':
                fido2_data = cbor.decode(b64decode(data.get('fido2Data')))
                auth_data = settings.FIDO2_SERVER.register_complete(
                    state=request.session['state'],
                    client_data=ClientData(fido2_data["clientDataJSON"]),
                    attestation_object=AttestationObject(fido2_data["attestationObject"])
                )

                mfa.description = data.get('description', ' ')
                mfa.mfa_data = websafe_encode(auth_data.credential_data)
                mfa.state = MfaKey.MFA_STATE_ENABLED

        # otherwise, you can enable/disable the key and change the description
        else:
            if 'description' in data:
                mfa.description = data.get('description')

            if 'enabled' in data:
                if data['enabled']:
                    mfa.state = MfaKey.MFA_STATE_ENABLED
                else:
                    mfa.state = MfaKey.MFA_STATE_DISABLED

        mfa.save()
        return HttpResponse(status=200)

    @method_decorator(login_required)
    def delete(self, request: HttpRequest, uuid, *args, **kwargs):
        MfaKey.objects.filter(uuid=uuid).delete()
        return HttpResponse(status=204)


class Login(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('base:home'))
        return render(request, 'login.html')

    def post(self, request: HttpRequest, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('base:home'))
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(json.dumps({}), status=400)

        if 'username' not in data or 'password' not in data:
            return HttpResponse(json.dumps({}), status=400)

        user: User = authenticate(username=data.get('username'), password=data.get('password'))
        if not user:
            return HttpResponse(json.dumps({
                "error": "invalid_credentials",
                "message": "Invalid Credentials",
            }), status=401)

        mfa_keys = MfaKey.objects.filter(user=user, state=MfaKey.MFA_STATE_ENABLED).all()

        # if the user does not have mfa configured
        if not mfa_keys:
            login(request, user)
            return redirect(reverse('base:home'))

        # if no mfa method has been submitted with the login information
        if 'mfaType' not in data:
            return HttpResponse(json.dumps({
                "error": "mfa_required",
                "type": list({mfa.type_name for mfa in mfa_keys}),
            }), status=401)

        # the user would like to perform mfa, now check which method the user tries to provide
        elif data['mfaType'] == 'totp' and 'token' in data:
            mfa_keys = MfaKey.objects.filter(user=user, type=get_type('totp'), state=MfaKey.MFA_STATE_ENABLED).all()

            # reduce the list by checking if the entered token is valid for the MfaKey
            found_valid_totp = False
            for mfa in mfa_keys:
                if not valid_totp(data['token'], mfa.mfa_data):
                    continue
                found_valid_totp = True
                mfa.last_used = timezone.now()
                mfa.save()
                login(request, user)
                return redirect(reverse('base:home'))

            if not found_valid_totp:
                return HttpResponse(json.dumps({
                    "error": "mfa_error",
                    "message": "Invalid TOTP Token",
                }), status=401)

        # the user would like to initiate fido2 auth, the server needs to send him a challenge
        elif data['mfaType'] == 'fido2' and 'fido2Data' not in data:
            mfa_keys = MfaKey.objects.filter(user=user, type=get_type('fido2'), state=MfaKey.MFA_STATE_ENABLED).all()
            credentials = [AttestedCredentialData(websafe_decode(mfa.mfa_data)) for mfa in mfa_keys]
            auth_data, state = settings.FIDO2_SERVER.authenticate_begin(credentials)
            request.session['state'] = state
            return HttpResponse(json.dumps({
                "fido2Data": b64encode(cbor.encode(auth_data)).decode(),
            }), status=200)

        # the user already initiated the fido2 auth and provides the challenge solution.
        # the server needs to validate the challenge
        elif data['mfaType'] == 'fido2' and 'fido2Data' in data:
            mfa_keys = MfaKey.objects.filter(user=user, type=get_type('fido2'), state=MfaKey.MFA_STATE_ENABLED).all()
            credentials = [AttestedCredentialData(websafe_decode(mfa.mfa_data)) for mfa in mfa_keys]
            fido2_data = cbor.decode(b64decode(data.get('fido2Data')))
            try:
                settings.FIDO2_SERVER.authenticate_complete(
                    request.session.pop('state'),
                    credentials,
                    fido2_data['credentialId'],
                    ClientData(fido2_data['clientDataJSON']),
                    AuthenticatorData(fido2_data['authenticatorData']),
                    fido2_data['signature']
                )
            except ValueError as e:
                return HttpResponse(json.dumps({
                    "error": "mfa_error",
                    "message": "Invalid FIDO2 Auth",
                }), status=401)

            # TODO only update the key that has been actually used
            #  But how to identify the key, which has been used to login?
            for key in mfa_keys:
                key.last_used = timezone.now()
                key.save()

            login(request, user)
            return redirect(reverse('base:home'))

        return HttpResponse(json.dumps({
            "error": "mfa_error",
            "message": "Invalid MFA setup",
        }), status=401)


class Logout(View):
    @method_decorator(login_required)
    def get(self, request: HttpRequest, *args, **kwargs):
        logout(request)
        return redirect(reverse('security:login'))
