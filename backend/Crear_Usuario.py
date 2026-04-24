from app.auth import hash_password

password = "123456"

hashed = hash_password(password)

print("Contraseña encriptada:")
print(hashed)
