# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import re
from unittest import mock

import numpy as np
import pytest
import torch

from flash import Trainer
from flash.audio import SpeechRecognition
from flash.audio.speech_recognition.data import SpeechRecognitionPostprocess, SpeechRecognitionPreprocess
from flash.core.data.data_source import DefaultDataKeys
from tests.helpers.utils import _AUDIO_TESTING, _SERVE_TESTING

# ======== Mock functions ========


class DummyDataset(torch.utils.data.Dataset):

    def __getitem__(self, index):
        return {
            DefaultDataKeys.INPUT: np.random.randn(86631),
            DefaultDataKeys.TARGET: "some target text",
            DefaultDataKeys.METADATA: {
                "sampling_rate": 16000
            },
        }

    def __len__(self) -> int:
        return 100


# ==============================

TEST_BACKBONE = "patrickvonplaten/wav2vec2_tiny_random_robust"  # super small model for testing


@pytest.mark.skipif(os.name == "nt", reason="Huggingface timing out on Windows")
@pytest.mark.skipif(not _AUDIO_TESTING, reason="audio libraries aren't installed.")
def test_init_train(tmpdir):
    model = SpeechRecognition(backbone=TEST_BACKBONE)
    train_dl = torch.utils.data.DataLoader(DummyDataset())
    trainer = Trainer(default_root_dir=tmpdir, fast_dev_run=True)
    trainer.fit(model, train_dl)


@pytest.mark.skipif(not _AUDIO_TESTING, reason="audio libraries aren't installed.")
def test_jit(tmpdir):
    sample_input = {"input_values": torch.randn(size=torch.Size([1, 86631])).float()}
    path = os.path.join(tmpdir, "test.pt")

    model = SpeechRecognition(backbone=TEST_BACKBONE)
    model.eval()

    # Huggingface model only supports `torch.jit.trace` with `strict=False`
    model = torch.jit.trace(model, sample_input, strict=False)

    torch.jit.save(model, path)
    model = torch.jit.load(path)

    out = model(sample_input)["logits"]
    assert isinstance(out, torch.Tensor)
    assert out.shape == torch.Size([1, 95, 12])


@pytest.mark.skipif(not _SERVE_TESTING, reason="serve libraries aren't installed.")
@pytest.mark.skipif(not _AUDIO_TESTING, reason="audio libraries aren't installed.")
@mock.patch("flash._IS_TESTING", True)
def test_serve():
    model = SpeechRecognition(backbone=TEST_BACKBONE)
    # TODO: Currently only servable once a preprocess and postprocess have been attached
    model._preprocess = SpeechRecognitionPreprocess()
    model._postprocess = SpeechRecognitionPostprocess()
    model.eval()
    model.serve()


@pytest.mark.skipif(_AUDIO_TESTING, reason="audio libraries are installed.")
def test_load_from_checkpoint_dependency_error():
    with pytest.raises(ModuleNotFoundError, match=re.escape("'lightning-flash[audio]'")):
        SpeechRecognition.load_from_checkpoint("not_a_real_checkpoint.pt")
