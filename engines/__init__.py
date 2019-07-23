
data_folder = 'engines/data'
tmp_folder = 'engines/tmp'
eval_folder = 'engines/eval'
valid_folder = 'engines/valid'
model_root = 'static/model'


def act_environ(engine):
    return {
            "kraken": 'source activate kraken',
            "ocropus": 'source activate ocropus_env',
            "calamari": 'source activate calamari'}[engine]


deact_environ = 'conda deactivate'
