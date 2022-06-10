"""
This is an attempt to sync two icloud photo libraries.
This is meant to put all my photos in Rezi's Photos Library and visa-versa.
"""
import logging
import os
import sys
import random

from dotenv import load_dotenv
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudAPIResponseException
from pyicloud.services.photos import PhotoAsset


def authenticate(user):
    api = PyiCloudService(os.environ[f"{user}"], os.environ[f'{user}_PASSWORD'])

    if api.requires_2fa:
        print("Two-factor authentication required.")
        code = input("Enter the code you received of one of your approved devices: ")
        result = api.validate_2fa_code(code)
        print("Code validation result: %s" % result)

        if not result:
            print("Failed to verify security code")
            sys.exit(1)

        if not api.is_trusted_session:
            print("Session is not trusted. Requesting trust...")
            result = api.trust_session()
            print("Session trust result %s" % result)

            if not result:
                print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")
    elif api.requires_2sa:
        import click
        print("Two-step authentication required. Your trusted devices are:")

        devices = api.trusted_devices
        for i, device in enumerate(devices):
            print("  %s: %s" % (i, device.get('deviceName',
                                              "SMS to %s" % device.get('phoneNumber'))))

        device = click.prompt('Which device would you like to use?', default=0)
        device = devices[device]
        if not api.send_verification_code(device):
            print("Failed to send verification code")
            sys.exit(1)

        code = click.prompt('Please enter validation code')
        if not api.validate_verification_code(device, code):
            print("Failed to verify verification code")
            sys.exit(1)
    return api


def get_photo(user: PyiCloudService):
    select = random.randint(0, 90)
    i = 0
    photos = user.photos.all.photos
    while i < select:
        next(photos)
        i += 1

    return next(photos)


def transfer_photo(user: PyiCloudService, photo: PhotoAsset):
    base_url = user.data["webservices"]["uploadimagews"]["url"]

    request = user.photos.session.post(
        url=f'{base_url}/upload',
        data=photo.download().raw.read(),
        headers={"Content-type": "text/plain"},
        params={
            'filename': photo.filename,
        }
    )

    request_json = request.json()

    if 'errors' in request_json:
        raise PyiCloudAPIResponseException('photo upload error', request_json['errors'])

    return request_json


def main():
    load_dotenv()

    logging.debug('auth user 1')
    user1 = authenticate('USER_1')
    logging.debug('auth user 2')
    user2 = authenticate('USER_2')

    photo = get_photo(user1)
    # get_photos(user2)

    request_json = transfer_photo(user2, photo)

    print(request_json)


if __name__ == '__main__':
    main()
    print('done')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
