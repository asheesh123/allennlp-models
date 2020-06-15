import logging
from typing import Dict

import torch
from allennlp.data import Vocabulary, TextFieldTensors
from allennlp.models import Model

logger = logging.getLogger(__name__)


@Model.register("transformer_mc")
class TransformerMC(Model):
    """
    This class implements a multiple choice model patterned after the proposed model in
    https://arxiv.org/abs/1810.04805 (Devlin et al).

    It calculates a score for each sequence on top of the CLS token, and then chooses the alternative with the highest
    score.

    Parameters
    ----------
    vocab : ``Vocabulary``
    transformer_model_name : ``str``, optional (default=``roberta-large``)
        This model chooses the embedder according to this setting. You probably want to make sure this is set to
        the same thing as the reader.
    """

    def __init__(
        self, vocab: Vocabulary, transformer_model_name: str = "roberta_large", **kwargs
    ) -> None:
        super().__init__(vocab, **kwargs)
        from allennlp.modules.text_field_embedders import BasicTextFieldEmbedder
        from allennlp.modules.token_embedders import PretrainedTransformerEmbedder

        self._text_field_embedder = BasicTextFieldEmbedder(
            {"tokens": PretrainedTransformerEmbedder(transformer_model_name)}
        )

        self._first_linear_layer = torch.nn.Linear(
            self._text_field_embedder.get_output_dim(),
            self._text_field_embedder.get_output_dim())
        self._second_linear_layer = torch.nn.Linear(self._text_field_embedder.get_output_dim(), 1)

        self._loss = torch.nn.CrossEntropyLoss()

        from allennlp.training.metrics import CategoricalAccuracy

        self._accuracy = CategoricalAccuracy()

    def forward(  # type: ignore
        self, alternatives: TextFieldTensors, correct_alternative: torch.IntTensor,
    ) -> Dict[str, torch.Tensor]:

        """
        Parameters
        ----------
        alternatives : ``Dict[str, torch.LongTensor]``
            From a ``ListField[TextField]``. Contains a list of alternatives to evaluate for every instance.
        correct_alternative : ``torch.IntTensor``
            From an ``IndexField``. Contains the index of the correct answer for every instance.

        Returns
        -------
        An output dictionary consisting of:
        loss : ``torch.FloatTensor``, optional
            A scalar loss to be optimised.
        best_alternative : ``List[int]``
            The index of the highest scoring alternative for every instance in the batch
        """
        embedded_alternatives = self._text_field_embedder(alternatives, num_wrapping_dims=1)
        flattened_embedded_alternatives = embedded_alternatives.view(
            embedded_alternatives.size(0) * embedded_alternatives.size(1),
            embedded_alternatives.size(2),
            embedded_alternatives.size(3)
        )
        flattened_pooled_alternatives = flattened_embedded_alternatives[:, 0]
        flattened_logit_alternatives = self._first_linear_layer(flattened_pooled_alternatives)
        flattened_logit_alternatives = torch.tanh(flattened_logit_alternatives)
        flattened_logit_alternatives = self._second_linear_layer(flattened_logit_alternatives)
        logit_alternatives = flattened_logit_alternatives.view(
            embedded_alternatives.size(0),
            embedded_alternatives.size(1)
        )

        correct_alternative = correct_alternative.squeeze(1)

        loss = self._loss(logit_alternatives, correct_alternative)
        self._accuracy(logit_alternatives, correct_alternative)

        return {"loss": loss}

    def get_metrics(self, reset: bool = False) -> Dict[str, float]:
        return {
            "acc": self._accuracy.get_metric(reset),
        }

    default_predictor = "transformer_mc"
