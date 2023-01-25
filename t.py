import mimetypes
mime_type = mimetypes.guess_type(r"C:\Users\Jigar\Desktop\Amazon Prime Dl\t.py")[0] or "video/mp4"
print(mime_type)