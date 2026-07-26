ROLE_SYSADMIN = "sysadmin"
ROLE_MANAGER = "manager"
ROLE_WORKER = "worker"

ROLE_LABELS = {
    ROLE_SYSADMIN: "维修管理员",
    ROLE_MANAGER: "维修管理员",
    ROLE_WORKER: "维修工"
}

fake_users = {
    "admin": {
        "username": "admin",
        "password": "ad1234",
        "role": ROLE_SYSADMIN,
        "fullname": "赵五"
    },
    "worker1": {
        "username": "worker1",
        "password": "123456",
        "role": ROLE_WORKER,
        "fullname": "李建华"
    },
    "worker2": {
        "username": "worker2",
        "password": "234567",
        "role": ROLE_WORKER,
        "fullname": "张伟"
    },
    "worker3": {
        "username": "worker3",
        "password": "345678",
        "role": ROLE_WORKER,
        "fullname": "黄丽"
    },
    "manager": {
        "username": "manager",
        "password": "123456",
        "role": ROLE_MANAGER,
        "fullname": "王主任"
    },
    "worker": {
        "username": "worker",
        "password": "123456",
        "role": ROLE_WORKER,
        "fullname": "李师傅"
    }
}


def get_user(username: str):
    u = fake_users.get(username)
    if not u:
        return None
    return {
        "username": u["username"],
        "role": u["role"],
        "fullname": u.get("fullname") or u["username"],
        "role_label": ROLE_LABELS.get(u["role"], u["role"])
    }


def verify_user(username: str, password: str):
    u = fake_users.get(username)
    if not u or u["password"] != password:
        return None
    return get_user(username)
