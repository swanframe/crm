from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """
    Menghasilkan hash untuk password yang diberikan.
    """
    return generate_password_hash(password)

def check_hashed_password(hashed_password, password):
    """
    Memverifikasi apakah password yang diberikan cocok dengan hash yang tersimpan.
    """
    return check_password_hash(hashed_password, password)