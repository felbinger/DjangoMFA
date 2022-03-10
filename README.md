# Django Multi-Factor Authentication

## Features
* TOTP and FIDO2 Authentication

## Preview

![](./resources/img/djangomfa-login.png)

There is a sample settings page where you can easily change some attributes of the user you are logged in with.
![](./resources/img/djangomfa-settings.png)

The security page allows you to manage multi-factor authentication keys.
![](./resources/img/djangomfa-security-without-keys.png)

You may choose between TOTP and FIDO2.
![](./resources/img/djangomfa-security-add-key-overview.png)

![](./resources/img/djangomfa-security-add-key-totp.png)

![](./resources/img/djangomfa-security-add-key-fido2.png)

![](./resources/img/djangomfa-security-add-key-fido2-description.png)

Besides the description, you may update the state (enabled or disabled) of the keys, you can also delete the mfa keys here.
![](./resources/img/djangomfa-security-update-key.png)

![](./resources/img/djangomfa-security-with-keys.png)

Logging in with mfa enabled means you have to complete one of the configured challenges (the modal where you can choose will only show up if more than one mfa key is configured).
![](./resources/img/djangomfa-login-totp-fido2.png)

![](./resources/img/djangomfa-login-totp.png)

![](./resources/img/djangomfa-login-fido2.png)
