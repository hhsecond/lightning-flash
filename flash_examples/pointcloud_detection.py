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
import flash
from flash.core.data.utils import download_data
from flash.pointcloud import PointCloudObjectDetector, PointCloudObjectDetectorData

# 1. Create the DataModule
# Dataset Credit: http://www.semantic-kitti.org/
download_data("https://pl-flash-data.s3.amazonaws.com/KITTI_tiny.zip", "data/")

datamodule = PointCloudObjectDetectorData.from_folders(
    train_folder="data/KITTI_Tiny/Kitti/train",
    val_folder="data/KITTI_Tiny/Kitti/val",
)

# 2. Build the task
model = PointCloudObjectDetector(backbone="pointpillars_kitti", num_classes=datamodule.num_classes)

# 3. Create the trainer and finetune the model
trainer = flash.Trainer(max_epochs=1, limit_train_batches=1, limit_val_batches=1, num_sanity_val_steps=0)
trainer.fit(model, datamodule)

# 4. Predict what's within a few PointClouds?
predictions = model.predict([
    "data/KITTI_Tiny/Kitti/predict/scans/000000.bin",
    "data/KITTI_Tiny/Kitti/predict/scans/000001.bin",
])

# 5. Save the model!
trainer.save_checkpoint("pointcloud_segmentation_model.pt")
