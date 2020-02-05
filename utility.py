from subprocess import check_output


def check_processes(list_of_processes):
    lines = check_output(['ps', 'aux']).decode().splitlines()
    procs = [l.split()[10] for l in lines]
    return all(p in procs for p in list_of_processes)


def check_sound_card(expected_dev):
    output = check_output(['aplay', '-l']).decode()
    return expected_dev in output


def check_midi(list_of_midi_devs):
    lines = check_output(['aconnect', '-i', '-o']).decode().splitlines()
    clients = [l for l in lines if l.startswith('client')]
    for m in list_of_midi_devs:
        if not any(m in c for c in clients):
            return False
    return True
