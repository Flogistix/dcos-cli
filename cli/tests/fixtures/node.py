def slave_fixture():
    """ Slave node fixture.

    :rtype: dict
    """

    return {
        "TASK_ERROR": 0,
        "TASK_FAILED": 0,
        "TASK_FINISHED": 0,
        "TASK_KILLED": 0,
        "TASK_LOST": 0,
        "TASK_RUNNING": 0,
        "TASK_STAGING": 0,
        "TASK_STARTING": 0,
        "active": True,
        "attributes": {},
        "framework_ids": [],
        "hostname": "dcos-01",
        "id": "20150630-004309-1695027628-5050-1649-S0",
        "offered_resources": {
            "cpus": 0,
            "disk": 0,
            "mem": 0
        },
        "pid": "slave(1)@172.17.8.101:5051",
        "registered_time": 1435625024.42234,
        "resources": {
            "cpus": 4,
            "disk": 10823,
            "mem": 2933,
            "ports": ("[1025-2180, 2182-3887, 3889-5049, 5052-8079, " +
                      "8082-8180, 8182-65535]")
        },
        "used_resources": {
            "cpus": 0,
            "disk": 0,
            "mem": 0
        }
    }
