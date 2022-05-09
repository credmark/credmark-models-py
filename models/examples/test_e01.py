from credmark.cmf.engine.model_unittest import ModelTestCase, model_context


class ExampleEchoTest(ModelTestCase):

    @model_context(chain_id=1, block_number=12345)
    def test_echo(self):

        # sanity check that the context is as expected
        self.assertEqual(self.context.block_number, 12345)

        # run the model
        message = 'echo-test'
        output = self.context.models.example.model(message=message)

        self.logger.debug(output)

        self.assertEqual(output['title'], '1. Example - Model')
        self.assertEqual(output['echo'],
                         f'{message} from block: {self.context.block_number}')
        self.assertIsNotNone(output.get('logs'))
