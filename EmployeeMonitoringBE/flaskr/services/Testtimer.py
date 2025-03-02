from threading import Timer

def delete_expired_or_verified_code(session, code_id):
    print("Ran timer")

def schedule_code_deletion(session, code_id):
    Timer(300, delete_expired_or_verified_code, args=[session, code_id]).start()
    print("timer started")
    return

schedule_code_deletion("session", 1)


# Se creeaza user-ul
# 