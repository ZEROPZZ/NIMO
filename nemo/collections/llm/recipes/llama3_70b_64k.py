# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
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


from typing import Optional

import lightning.pytorch as pl
import nemo_run as run
import torch

from nemo.collections.llm.api import finetune, pretrain
from nemo.collections.llm.gpt.data.mock import MockDataModule
from nemo.collections.llm.recipes import llama3_70b
from nemo.utils.exp_manager import TimingCallback

NAME = "llama3_70b_64k"


@run.cli.factory(name=NAME)
def model() -> run.Config[pl.LightningModule]:
    """
    Factory function to create a Llama3 70B model configuration with 64k sequence length.

    Returns:
        run.Config[pl.LightningModule]: Configuration for the Llama3 70B model with 64k sequence length.

    Examples:
        CLI usage:
            $ nemo llm pretrain model=llama3_70b_64k ...

        Python API usage:
            >>> model_config = model()
            >>> print(model_config)
    """
    model_config = llama3_70b.model()
    model_config.config.seq_length = 65536
    return model_config


def trainer(
    num_nodes: int = 32,
    num_gpus_per_node: int = 8,
) -> run.Config:
    """
    Configure the NeMo Lightning Trainer for Llama3 70B model with 64k sequence length.

    This function sets up the distributed training strategy optimized for the large 70B model with long sequences.

    Args:
        num_nodes (int, optional): Number of compute nodes to use. Defaults to 32.
        num_gpus_per_node (int, optional): Number of GPUs per node. Defaults to 8.

    Returns:
        run.Config: Configuration for the NeMo Lightning Trainer.

    Examples:
        CLI usage:
            $ nemo llm pretrain trainer=llama3_70b_64k ...

        Python API usage:
            >>> trainer_config = trainer(num_nodes=32, num_gpus_per_node=8)
            >>> print(trainer_config)

    Note:
        This configuration uses extensive parallelism to handle the large model size and long sequence length efficiently.
        It requires a significant amount of computational resources.
    """
    return llama3_70b.trainer(
        tensor_parallelism=8,
        pipeline_parallelism=4,
        pipeline_parallelism_type=torch.bfloat16,
        virtual_pipeline_parallelism=None,
        context_parallelism=8,
        sequence_parallelism=True,
        num_nodes=num_nodes,
        num_gpus_per_node=num_gpus_per_node,
        callbacks=[run.Config(TimingCallback)],
    )


@run.cli.factory(target=pretrain, name=NAME)
def pretrain_recipe(
    dir: Optional[str] = None,
    name: str = "default",
    num_nodes: int = 32,
    num_gpus_per_node: int = 8,
) -> run.Partial:
    """
    Create a pre-training recipe for Llama3 70B model with 64k sequence length.

    This function sets up a complete configuration for pre-training, including
    model, trainer, and data settings optimized for 64k sequence length.

    Args:
        dir (Optional[str]): Directory for saving logs and checkpoints.
        name (str): Name of the pre-training run.
        num_nodes (int, optional): Number of compute nodes to use. Defaults to 32.
        num_gpus_per_node (int, optional): Number of GPUs per node. Defaults to 8.

    Returns:
        run.Partial: Partial configuration for pre-training.

    Examples:
        CLI usage:
            $ nemo llm pretrain --factory llama3_70b_64k
            $ nemo llm pretrain --factory "llama3_70b_64k(num_nodes=32, name='my_70b_64k_pretrain')"

        Python API usage:
            >>> recipe = pretrain_recipe(name="llama3_70b_64k_pretrain", num_nodes=32)
            >>> print(recipe)

    Note:
        This recipe is optimized for the large 70B model with long sequences (64k).
        It requires extensive computational resources due to the model size and extended sequence length.
    """
    recipe = llama3_70b.pretrain_recipe(name=name, dir=dir, num_nodes=num_nodes, num_gpus_per_node=num_gpus_per_node)

    recipe.model = model()
    recipe.trainer = trainer(num_nodes=num_nodes, num_gpus_per_node=num_gpus_per_node)
    recipe.data = run.Config(MockDataModule, seq_length=65536, global_batch_size=512, micro_batch_size=1)

    return recipe