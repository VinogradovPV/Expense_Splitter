# Cloud Scripts

These scripts are safe local helpers for CLOUD.8. They do not create Yandex Cloud
resources, do not upload artifacts, and do not read plaintext secrets from the repository.

Use real cloud deployment commands only after explicit operator approval and with secrets
provided through Yandex Lockbox or environment variables outside Git.
