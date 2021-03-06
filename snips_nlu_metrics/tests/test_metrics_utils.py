from __future__ import division
from __future__ import unicode_literals

import unittest
from builtins import object

from snips_nlu_metrics.utils.constants import (TRUE_POSITIVE, FALSE_POSITIVE,
                                               FALSE_NEGATIVE, TEXT)
from snips_nlu_metrics.utils.metrics_utils import (
    aggregate_metrics, compute_utterance_metrics, compute_precision_recall_f1,
    exact_match, contains_errors, compute_engine_metrics, aggregate_matrices)


class TestMetricsUtils(unittest.TestCase):
    def test_should_compute_engine_metrics(self):
        # Given
        def create_utterance(intent_name, slot_name, slot_value):
            utterance = {
                "data": [
                    {
                        "text": "this is an utterance with ",
                    },
                    {
                        "text": slot_value,
                        "slot_name": slot_name,
                        "entity": slot_name
                    }
                ]
            }
            return intent_name, utterance

        def create_parsing_output(intent_name, slot_name, slot_value):
            return {
                "text": "this is an utterance with %s" % slot_value,
                "intent": {
                    "intentName": intent_name,
                    "probability": 1.0
                },
                "slots": [{
                    "rawValue": slot_value,
                    "range": {"start": 26, "end": 26 + len(slot_value)},
                    "entity": slot_name,
                    "slotName": slot_name
                }]
            }

        utterances = [
            create_utterance("intent1", "slot1", "value1"),
            create_utterance("intent1", "slot1", "value2"),
            create_utterance("intent1", "slot2", "value3"),
            create_utterance("intent2", "slot3", "value4"),
            create_utterance("intent2", "slot3", "value5"),
        ]

        class TestEngine(object):
            def __init__(self):
                self.utterance_index = 0

            def parse(self, text):
                res = None
                if self.utterance_index == 0:
                    res = create_parsing_output("intent1", "slot1", "value1")
                if self.utterance_index == 1:
                    res = create_parsing_output("intent2", "slot3", "value4")
                if self.utterance_index == 2:
                    res = create_parsing_output("intent1", "slot1", "value1")
                if self.utterance_index == 3:
                    res = create_parsing_output("intent2", "slot3", "value4")
                if self.utterance_index == 4:
                    res = create_parsing_output("intent2", "slot3", "value4")
                self.utterance_index += 1
                return res

        engine = TestEngine()

        def slots_match(lhs, rhs):
            return lhs[TEXT] == rhs["rawValue"]

        # When
        metrics, errors, confusion_matrix = compute_engine_metrics(
            engine=engine, test_utterances=utterances,
            intent_list=["intent1", "intent2"], include_slot_metrics=True,
            slot_matching_lambda=slots_match)

        # Then
        expected_metrics = {
            "intent1": {
                "slots": {
                    "slot1": {
                        "false_positive": 1,
                        "true_positive": 1,
                        "false_negative": 0
                    },
                    "slot2": {
                        "false_positive": 0,
                        "true_positive": 0,
                        "false_negative": 1
                    }
                },
                "intent": {
                    "false_positive": 0,
                    "true_positive": 2,
                    "false_negative": 1
                }
            },
            "intent2": {
                "slots": {
                    "slot3": {
                        "false_positive": 1,
                        "true_positive": 1,
                        "false_negative": 1
                    }
                },
                "intent": {
                    "false_positive": 1,
                    "true_positive": 2,
                    "false_negative": 0
                }
            }
        }
        expected_errors = [
            {
                "expected_output": {
                    "input": "this is an utterance with value2",
                    "slots": [
                        {
                            "range": {
                                "start": 26,
                                "end": 32
                            },
                            "slotName": "slot1",
                            "rawValue": "value2",
                            "entity": "slot1"
                        }
                    ],
                    "intent": {
                        "intentName": "intent1",
                        "probability": 1.0
                    }
                },
                "nlu_output": {
                    "text": "this is an utterance with value4",
                    "slots": [
                        {
                            "slotName": "slot3",
                            "range": {
                                "start": 26,
                                "end": 32
                            },
                            "rawValue": "value4",
                            "entity": "slot3"
                        }
                    ],
                    "intent": {
                        "intentName": "intent2",
                        "probability": 1.0
                    }
                }
            },
            {
                "expected_output": {
                    "input": "this is an utterance with value3",
                    "slots": [
                        {
                            "range": {
                                "start": 26,
                                "end": 32
                            },
                            "slotName": "slot2",
                            "rawValue": "value3",
                            "entity": "slot2"
                        }
                    ],
                    "intent": {
                        "intentName": "intent1",
                        "probability": 1.0
                    }
                },
                "nlu_output": {
                    "text": "this is an utterance with value1",
                    "slots": [
                        {
                            "slotName": "slot1",
                            "range": {
                                "start": 26,
                                "end": 32
                            },
                            "rawValue": "value1",
                            "entity": "slot1"
                        }
                    ],
                    "intent": {
                        "intentName": "intent1",
                        "probability": 1.0
                    }
                }
            },
            {
                "expected_output": {
                    "input": "this is an utterance with value5",
                    "slots": [
                        {
                            "range": {
                                "start": 26,
                                "end": 32
                            },
                            "slotName": "slot3",
                            "rawValue": "value5",
                            "entity": "slot3"
                        }
                    ],
                    "intent": {
                        "intentName": "intent2",
                        "probability": 1.0
                    }
                },
                "nlu_output": {
                    "text": "this is an utterance with value4",
                    "slots": [
                        {
                            "slotName": "slot3",
                            "range": {
                                "start": 26,
                                "end": 32
                            },
                            "rawValue": "value4",
                            "entity": "slot3"
                        }
                    ],
                    "intent": {
                        "intentName": "intent2",
                        "probability": 1.0
                    }
                }
            }
        ]

        expected_confusion_matrix = {
            "intents": [
                "intent1",
                "intent2",
                "null"
            ],
            "matrix": [
                [2, 1, 0],
                [0, 2, 0],
                [0, 0, 0],
            ]
        }

        self.assertDictEqual(expected_metrics, metrics)
        self.assertListEqual(expected_errors, errors)
        self.assertDictEqual(expected_confusion_matrix, confusion_matrix)

    def test_should_compute_utterance_metrics_when_wrong_intent(self):
        # Given
        text = "utterance of intent1"
        actual_intent = "intent1"
        actual_slots = []
        predicted_intent = "intent2"
        predicted_slots = [
            {
                "rawValue": "utterance",
                "value": {
                    "kind": "Custom",
                    "value": "utterance"
                },
                "range": {
                    "start": 0,
                    "end": 9
                },
                "entity": "erroneous_entity",
                "slotName": "erroneous_slot"
            }
        ]

        # When
        metrics = compute_utterance_metrics(predicted_intent, predicted_slots,
                                            actual_intent, actual_slots,
                                            True, exact_match)
        # Then
        expected_metrics = {
            "intent1": {
                "intent": {
                    "false_negative": 1,
                    "false_positive": 0,
                    "true_positive": 0
                },
                "slots": {}
            },
            "intent2": {
                "intent": {
                    "false_negative": 0,
                    "false_positive": 1,
                    "true_positive": 0
                },
                "slots": {
                    "erroneous_slot": {
                        "false_negative": 0,
                        "false_positive": 0,
                        "true_positive": 0
                    }
                }
            }
        }

        self.assertDictEqual(expected_metrics, metrics)

    def test_should_compute_utterance_metrics_when_correct_intent(self):
        # Given
        text = "this is intent1 with slot1_value and slot2_value"
        actual_intent = "intent1"
        actual_slots = [
            {
                "text": "slot1_value",
                "entity": "entity1",
                "slot_name": "slot1"
            },
            {
                "text": "slot2_value",
                "entity": "entity2",
                "slot_name": "slot2"
            }
        ]
        predicted_intent = actual_intent
        predicted_slots = [
            {
                "rawValue": "slot1_value",
                "value": {
                    "kind": "Custom",
                    "value": "slot1_value"
                },
                "range": {
                    "start": 21,
                    "end": 32
                },
                "entity": "entity1",
                "slotName": "slot1"
            }
        ]

        # When
        metrics = compute_utterance_metrics(predicted_intent, predicted_slots,
                                            actual_intent, actual_slots, True,
                                            exact_match)
        # Then
        expected_metrics = {
            "intent1": {
                "intent": {
                    "false_negative": 0,
                    "false_positive": 0,
                    "true_positive": 1
                },
                "slots": {
                    "slot1": {
                        "false_negative": 0,
                        "false_positive": 0,
                        "true_positive": 1
                    },
                    "slot2": {
                        "false_negative": 1,
                        "false_positive": 0,
                        "true_positive": 0
                    }
                }
            }
        }

        self.assertDictEqual(expected_metrics, metrics)

    def test_should_exclude_slot_metrics_when_specified(self):
        # Given
        text = "this is intent1 with slot1_value and slot2_value"
        actual_intent = "intent1"
        actual_slots = [
            {
                "text": "slot1_value",
                "entity": "entity1",
                "slot_name": "slot1"
            },
            {
                "text": "slot2_value",
                "entity": "entity2",
                "slot_name": "slot2"
            }
        ]
        predicted_intent = actual_intent
        predicted_slots = [
            {
                "rawValue": "slot1_value",
                "value": {
                    "kind": "Custom",
                    "value": "slot1_value"
                },
                "range": {"start": 21, "end": 32},
                "entity": "entity1",
                "slotName": "slot1"
            }
        ]

        # When
        include_slot_metrics = False
        metrics = compute_utterance_metrics(predicted_intent, predicted_slots,
                                            actual_intent, actual_slots,
                                            include_slot_metrics, exact_match)
        # Then
        expected_metrics = {
            "intent1": {
                "intent": {
                    "false_negative": 0,
                    "false_positive": 0,
                    "true_positive": 1
                }
            }
        }

        self.assertDictEqual(expected_metrics, metrics)

    def test_should_use_slot_matching_lambda_to_compute_metrics(self):
        # Given
        text = "this is intent1 with slot1_value and slot2_value"
        actual_intent = "intent1"
        actual_slots = [
            {
                "text": "slot1_value2",
                "entity": "entity1",
                "slot_name": "slot1"
            },
            {
                "text": "slot2_value",
                "entity": "entity2",
                "slot_name": "slot2"
            }
        ]
        predicted_intent = actual_intent
        predicted_slots = [
            {
                "rawValue": "slot1_value",
                "value": {
                    "kind": "Custom",
                    "value": "slot1_value"
                },
                "range": {
                    "start": 21,
                    "end": 32
                },
                "entity": "entity1",
                "slotName": "slot1"
            }
        ]

        def slot_matching_lambda(l, r):
            return l[TEXT].split("_")[0] == r["rawValue"].split("_")[0]

        # When
        metrics = compute_utterance_metrics(predicted_intent, predicted_slots,
                                            actual_intent, actual_slots,
                                            True, slot_matching_lambda)
        # Then
        expected_metrics = {
            "intent1": {
                "intent": {
                    "false_negative": 0,
                    "false_positive": 0,
                    "true_positive": 1
                },
                "slots": {
                    "slot1": {
                        "false_negative": 0,
                        "false_positive": 0,
                        "true_positive": 1
                    },
                    "slot2": {
                        "false_negative": 1,
                        "false_positive": 0,
                        "true_positive": 0
                    }
                }
            }
        }

        self.assertDictEqual(expected_metrics, metrics)

    def test_aggregate_utils_should_work(self):
        # Given
        lhs_metrics = {
            "intent1": {
                "intent": {
                    "false_positive": 4,
                    "true_positive": 6,
                    "false_negative": 9
                },
                "slots": {
                    "slot1": {
                        "false_positive": 1,
                        "true_positive": 2,
                        "false_negative": 3
                    },
                },
            },
            "intent2": {
                "intent": {
                    "false_positive": 3,
                    "true_positive": 2,
                    "false_negative": 5
                },
                "slots": {
                    "slot2": {
                        "false_positive": 4,
                        "true_positive": 2,
                        "false_negative": 2
                    },
                }
            },
        }

        rhs_metrics = {
            "intent1": {
                "intent": {
                    "false_positive": 3,
                    "true_positive": 3,
                    "false_negative": 3
                },
                "slots": {
                    "slot1": {
                        "false_positive": 2,
                        "true_positive": 3,
                        "false_negative": 1
                    },
                }
            },
            "intent2": {
                "intent": {
                    "false_positive": 4,
                    "true_positive": 5,
                    "false_negative": 6
                },
                "slots": {}
            },
            "intent3": {
                "intent": {
                    "false_positive": 1,
                    "true_positive": 7,
                    "false_negative": 2
                },
                "slots": {}
            },
        }

        # When
        aggregated_metrics = aggregate_metrics(lhs_metrics, rhs_metrics, True)

        # Then
        expected_metrics = {
            "intent1": {
                "intent": {
                    "false_positive": 7,
                    "true_positive": 9,
                    "false_negative": 12,
                },
                "slots":
                    {
                        "slot1": {
                            "false_positive": 3,
                            "true_positive": 5,
                            "false_negative": 4
                        },
                    }
            },
            "intent2": {
                "intent": {
                    "false_positive": 7,
                    "true_positive": 7,
                    "false_negative": 11,
                },
                "slots": {
                    "slot2": {
                        "false_positive": 4,
                        "true_positive": 2,
                        "false_negative": 2
                    },
                }
            },
            "intent3": {
                "intent": {
                    "false_positive": 1,
                    "true_positive": 7,
                    "false_negative": 2
                },
                "slots": {}
            },
        }

        self.assertDictEqual(expected_metrics, aggregated_metrics)

    def test_should_compute_precision_and_recall_and_f1(self):
        # Given
        metrics = {
            "intent1": {
                "intent": {
                    "false_positive": 7,
                    "true_positive": 9,
                    "false_negative": 12,
                },
                "slots":
                    {
                        "slot1": {
                            "false_positive": 3,
                            "true_positive": 5,
                            "false_negative": 4
                        },
                    }
            },
            "intent2": {
                "intent": {
                    "false_positive": 7,
                    "true_positive": 7,
                    "false_negative": 11,
                },
                "slots": {
                    "slot2": {
                        "false_positive": 4,
                        "true_positive": 2,
                        "false_negative": 2
                    },
                }
            },
        }

        # When
        augmented_metrics = compute_precision_recall_f1(metrics)

        # Then
        expected_metrics = {
            "intent1": {
                "intent": {
                    "false_positive": 7,
                    "true_positive": 9,
                    "false_negative": 12,
                    "precision": 9. / (7. + 9.),
                    "recall": 9. / (12. + 9.),
                    "f1": 2 * (9. / (7. + 9.)) * (9. / (12. + 9.)) / (
                            9. / (7. + 9.) + 9. / (12. + 9.))

                },
                "slots":
                    {
                        "slot1": {
                            "false_positive": 3,
                            "true_positive": 5,
                            "false_negative": 4,
                            "precision": 5. / (5. + 3.),
                            "recall": 5. / (5. + 4.),
                            "f1": 2 * (5. / (5. + 3.)) * (5. / (5. + 4.)) / (
                                    5. / (5. + 3.) + 5. / (5. + 4.))
                        },
                    }
            },
            "intent2": {
                "intent": {
                    "false_positive": 7,
                    "true_positive": 7,
                    "false_negative": 11,
                    "precision": 7. / (7. + 7.),
                    "recall": 7. / (7. + 11.),
                    "f1": 2 * (7. / (7. + 7.)) * (7. / (7. + 11.)) / (
                            7. / (7. + 7.) + 7. / (7. + 11.))
                },
                "slots": {
                    "slot2": {
                        "false_positive": 4,
                        "true_positive": 2,
                        "false_negative": 2,
                        "precision": 2. / (2. + 4.),
                        "recall": 2. / (2. + 2.),
                        "f1": 2 * (2. / (2. + 4.)) * (2. / (2. + 2.)) / (
                                2. / (2. + 4.) + 2. / (2. + 2.))
                    },
                }
            },
        }
        self.assertDictEqual(expected_metrics, augmented_metrics)

    def test_contains_errors_should_work_when_errors_in_intent(self):
        # Given
        utterance_metrics = {
            "intent1": {
                "intent": {
                    TRUE_POSITIVE: 5,
                    FALSE_POSITIVE: 1,
                    FALSE_NEGATIVE: 0
                },
                "slots": {
                    "slot1": {
                        TRUE_POSITIVE: 3,
                        FALSE_POSITIVE: 0,
                        FALSE_NEGATIVE: 0
                    }
                }
            },
            "intent2": {
                "intent": {
                    TRUE_POSITIVE: 20,
                    FALSE_POSITIVE: 0,
                    FALSE_NEGATIVE: 0
                },
                "slots": {}
            }
        }

        # When
        res = contains_errors(utterance_metrics, True)

        # Then
        self.assertTrue(res)

    def test_contains_errors_should_work_when_errors_in_slots(self):
        # Given
        utterance_metrics = {
            "intent1": {
                "intent": {
                    TRUE_POSITIVE: 5,
                    FALSE_POSITIVE: 0,
                    FALSE_NEGATIVE: 0
                },
                "slots": {
                    "slot1": {
                        TRUE_POSITIVE: 3,
                        FALSE_POSITIVE: 0,
                        FALSE_NEGATIVE: 0
                    },
                    "slot2": {
                        TRUE_POSITIVE: 3,
                        FALSE_POSITIVE: 0,
                        FALSE_NEGATIVE: 2
                    },
                }
            },
            "intent2": {
                "intent": {
                    TRUE_POSITIVE: 20,
                    FALSE_POSITIVE: 0,
                    FALSE_NEGATIVE: 0
                },
                "slots": {}
            }
        }

        # When
        res = contains_errors(utterance_metrics, True)

        # Then
        self.assertTrue(res)

    def test_contains_errors_should_work_when_no_errors(self):
        # Given
        utterance_metrics = {
            "intent1": {
                "intent": {
                    TRUE_POSITIVE: 5,
                    FALSE_POSITIVE: 0,
                    FALSE_NEGATIVE: 0
                },
                "slots": {
                    "slot1": {
                        TRUE_POSITIVE: 3,
                        FALSE_POSITIVE: 0,
                        FALSE_NEGATIVE: 0
                    },
                    "slot2": {
                        TRUE_POSITIVE: 3,
                        FALSE_POSITIVE: 0,
                        FALSE_NEGATIVE: 0
                    },
                }
            },
            "intent2": {
                "intent": {
                    TRUE_POSITIVE: 20,
                    FALSE_POSITIVE: 0,
                    FALSE_NEGATIVE: 0
                },
                "slots": {}
            }
        }

        # When
        res = contains_errors(utterance_metrics, True)

        # Then
        self.assertFalse(res)

    def test_contains_errors_should_not_check_slots_when_specified(self):
        # Given
        utterance_metrics = {
            "intent1": {
                "intent": {
                    TRUE_POSITIVE: 5,
                    FALSE_POSITIVE: 0,
                    FALSE_NEGATIVE: 0
                },
                "slots": {
                    "slot1": {
                        TRUE_POSITIVE: 3,
                        FALSE_POSITIVE: 0,
                        FALSE_NEGATIVE: 0
                    },
                    "slot2": {
                        TRUE_POSITIVE: 3,
                        FALSE_POSITIVE: 0,
                        FALSE_NEGATIVE: 2
                    },
                }
            }
        }

        # When
        check_slots = False
        res = contains_errors(utterance_metrics, check_slots)

        # Then
        self.assertFalse(res)

    def test_aggregate_matrix(self):
        # Given
        lhs_confusion_matrix = {
            "intents": [
                "intent1",
                "intent2",
                "intent3"
            ],
            "matrix": [
                [1, 10, 5],
                [3, 0, 4],
                [7, 8, 1]
            ]
        }

        rhs_confusion_matrix = {
            "intents": [
                "intent1",
                "intent2",
                "intent3"
            ],
            "matrix": [
                [3, 3, 3],
                [2, 7, 1],
                [9, 0, 1]
            ]
        }

        # When
        acc_matrix = aggregate_matrices(lhs_confusion_matrix,
                                        rhs_confusion_matrix)

        # Then
        expected_confusion_matrix = {
            "intents": [
                "intent1",
                "intent2",
                "intent3"
            ],
            "matrix": [
                [4, 13, 8],
                [5, 7, 5],
                [16, 8, 2]
            ]
        }

        self.assertDictEqual(expected_confusion_matrix, acc_matrix)
