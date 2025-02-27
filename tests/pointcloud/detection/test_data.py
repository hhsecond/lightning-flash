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
from os.path import join

import pytest
import torch
from pytorch_lightning import seed_everything

from flash import Trainer
from flash.core.data.data_source import DefaultDataKeys
from flash.core.data.utils import download_data
from flash.pointcloud.detection import PointCloudObjectDetector, PointCloudObjectDetectorData
from tests.helpers.utils import _POINTCLOUD_TESTING

if _POINTCLOUD_TESTING:
    from flash.pointcloud.detection.open3d_ml.backbones import ObjectDetectBatchCollator


@pytest.mark.skipif(not _POINTCLOUD_TESTING, reason="pointcloud libraries aren't installed")
def test_pointcloud_object_detection_data(tmpdir):

    seed_everything(52)

    download_data("https://pl-flash-data.s3.amazonaws.com/KITTI_micro.zip", tmpdir)

    dm = PointCloudObjectDetectorData.from_folders(train_folder=join(tmpdir, "KITTI_Micro", "Kitti", "train"), )

    class MockModel(PointCloudObjectDetector):

        def training_step(self, batch, batch_idx: int):
            assert isinstance(batch, ObjectDetectBatchCollator)
            assert len(batch.point) == 2
            assert batch.point[0][1].shape == torch.Size([4])
            assert len(batch.bboxes) > 1
            assert batch.attr[0]["name"] == '000000.bin'
            assert batch.attr[1]["name"] == '000001.bin'

    num_classes = 19
    model = MockModel(backbone="pointpillars_kitti", num_classes=num_classes)
    trainer = Trainer(max_epochs=1, limit_train_batches=1, limit_val_batches=0)
    trainer.fit(model, dm)

    predict_path = join(tmpdir, "KITTI_Micro", "Kitti", "predict")
    model.eval()

    predictions = model.predict([join(predict_path, "scans/000000.bin")])
    assert torch.stack(predictions[0][DefaultDataKeys.INPUT]).shape[1] == 4
    assert len(predictions[0][DefaultDataKeys.PREDS]) == 158
    assert predictions[0][DefaultDataKeys.PREDS][0].__dict__["identifier"] == 'box:1'
