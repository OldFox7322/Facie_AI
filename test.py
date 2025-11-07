import boto3

s3 = boto3.client('s3', region_name='eu-north-1')

# Завантажити файл
s3.upload_file('test.txt', 'photos-bd-7322', 'friends_folder/test.txt')

# Зчитати файл
s3.download_file('photos-bd-7322', 'friends_folder/test.txt', 'downloaded_test.txt')

print("✅ Успіх! Файл завантажено та зчитано.")