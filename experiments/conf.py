#PM: TODO Refactor this

def get_storage_url(host):
    if host == "pascal-tower01.intra.codilime.com":
        return '/home/piotr.milos/storage/Videos'
    elif host == "piotr-milos-pc.dhcp.intra.codilime.com":
        return '/home/piotr/storage/Videos'
    elif host == "cpascal":
        return '/home/maciek/mhome/ml_robotics_pmilos/'
    elif host == "houston":
        return '/home/maciek/local_mhome/ml_robotics_pmilos/'
    elif 'pro.cyfronet.pl' in host:
        return
    else:
        return '/tmp/'
        raise RuntimeError('Unknown host {}'.format(host))


PLGRID_STORAGE_URL = '/net/scratch/people/plghenrykm/pmilos/ppo_experiments'
PLGRID_STORAGE_URL = '/net/archive/groups/plggatari/scratch'
EAGLE_STORAGE_URL = '/home/plgrid/plgtgrel/rl/storage'
plgrid_neptune_conf = '''
export NEPTUNE_HOST=neptune.kdm.cyfronet.pl
export NEPTUNE_PORT=443
export NEPTUNE_USER=mklimek
export NEPTUNE_PASSWORD=UugfhOYPe1XL7mq98cpU
'''

with open('/tmp/plgrid_neptune.conf', 'w') as f:
    f.write(plgrid_neptune_conf)

plgrid_neptune_conf = '''
export NEPTUNE_HOST=kdm3.neptune.deepsense.io
export NEPTUNE_PORT=443
export NEPTUNE_USER=maciej.klimek@codilime.com
export NEPTUNE_PASSWORD=ooboo3iabaiGhee0
'''

with open('/tmp/plgrid_neptune_kdm3.conf', 'w') as f:
    f.write(plgrid_neptune_conf)

plgrid_neptune_conf = '''
export NEPTUNE_HOST=kdm3a.neptune.deepsense.io
export NEPTUNE_PORT=443
export NEPTUNE_USER=maciej.klimek@codilime.com
export NEPTUNE_PASSWORD=ooboo3iabaiGhee0
'''

with open('/tmp/plgrid_neptune_kdm3a.conf', 'w') as f:
    f.write(plgrid_neptune_conf)


plgrid_neptune_conf = '''
export NEPTUNE_HOST=kdm2.neptune.deepsense.io
export NEPTUNE_PORT=443
export NEPTUNE_USER=maciej.klimek@codilime.com
export NEPTUNE_PASSWORD=ooboo3iabaiGhee0
'''

with open('/tmp/plgrid_neptune_kdm2.conf', 'w') as f:
    f.write(plgrid_neptune_conf)

plgrid_neptune_conf = '''
export NEPTUNE_HOST=kdm2a.neptune.deepsense.io
export NEPTUNE_PORT=443
export NEPTUNE_USER=maciej.klimek@codilime.com
export NEPTUNE_PASSWORD=ooboo3iabaiGhee0
'''

with open('/tmp/plgrid_neptune_kdm2_a.conf', 'w') as f:
    f.write(plgrid_neptune_conf)


ml_neptune_conf = '''
export NEPTUNE_HOST=ml.neptune.deepsense.io
export NEPTUNE_PORT=443
export NEPTUNE_USER=piotr.milos@codilime.com
export NEPTUNE_PASSWORD=plosos2n
'''

with open('/tmp/ml_neptune.conf', 'w') as f:
    f.write(ml_neptune_conf)


kdmi_pm_neptune_conf = '''
export NEPTUNE_HOST=kdmi.neptune.deepsense.io
export NEPTUNE_PORT=443
export NEPTUNE_USER=piotr.milos@codilime.com
export NEPTUNE_PASSWORD=es5quoo7QuiP9Oph
'''

with open('/tmp/kdmi_pm_neptune.conf', 'w') as f:
    f.write(kdmi_pm_neptune_conf)

kdmi_hm_neptune_conf = '''
export NEPTUNE_HOST=kdmi.neptune.deepsense.io
export NEPTUNE_PORT=443
export NEPTUNE_USER=henryk.michalewski@codilime.com
export NEPTUNE_PASSWORD=ca4vaehahx1Jeib8
'''

with open('/tmp/kdmi_hm_neptune.conf', 'w') as f:
    f.write(kdmi_hm_neptune_conf)


