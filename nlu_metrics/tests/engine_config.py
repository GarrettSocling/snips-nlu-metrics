from __future__ import unicode_literals

NLU_CONFIG = {
    'intent_classifier_config': {
        'data_augmentation_config': {
            'min_utterances': 20,
            'noise_factor': 5
        },
        'featurizer_config': {
            'sublinear_tf': False
        },
        'log_reg_args': {
            'class_weight': 'balanced',
            'loss': 'log',
            'n_iter': 5,
            'n_jobs': -1,
            'penalty': 'l2',
            'random_state': 42
        }
    },
    'probabilistic_intent_parser_config': {
        'crf_features_config': {
            'base_drop_ratio': 0.0,
            'entities_offsets': [-2, -1, 0]
        },
        'data_augmentation_config': {
            'capitalization_ratio': 0.0,
            'min_utterances': 200
        }
    },
    'regex_training_config': {
        'max_entities': 200,
        'max_queries': 50
    }
}