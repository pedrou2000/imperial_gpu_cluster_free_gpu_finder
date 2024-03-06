SSH_USERNAME = 'pu22'
SSH_KEY_FILEPATH = '/home/pedro/.ssh/id_rsa'
SSH_JUMP_HOSTS = ['shell'+str(i)+'.doc.ic.ac.uk' for i in range(1, 6)]
TARGETS = ['gpu' + str(i) for i in range(25,37)]