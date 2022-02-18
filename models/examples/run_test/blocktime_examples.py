# import credmark.model
# from credmark.types.data.block_number import BlockNumber


# @credmark.model.it(slug='blocktime',
#                    version='1.0',
#                    display_name='Blocktime',
#                    description='The Time of the block of the execution context')
# class BlockTimeExample(credmark.model.Model):

#     """
#     This example returns the timestamp of the block that is contextualized.
#     """

#     def run(self, input) -> dict:

#         return {
#             "blockNumber": self.context.block_number,
#             "blockTime": self.context.block_number.timestamp,
#             "blockDateTime": str(self.context.block_number.to_datetime),
#             "tenThousandBlocksAgo": self.context.block_number - 10000,
#             "tenThousandBlocksAgoTimestamp": (self.context.block_number - 10000).timestamp,
#             "tenThousandBlocksAgoDateTime": str((self.context.block_number - 10000).to_datetime)
#         }


# @credmark.model.it(slug='blockrange',
#                    version='1.0',
#                    display_name='Blockrange',
#                    description='The Time of the block of the execution context')
# class BlockRangeExample(credmark.model.Model):

#     """
#     This example returns a range of BlockNumbers.
#     """

#     def run(self, input) -> dict:

#         return self.context.run_model("rpc.get-blockrange", {
#             "start": (self.context.block_number - 100000).timestamp,
#             "end": self.context.block_number.timestamp,
#             "interval": 10000
#         })


# @credmark.model.it(slug='sample-a-blocknumber',
#                    version='1.0',
#                    display_name='Blocktime',
#                    description='The Time of the block of the execution context')
# class SampledBlockNumberExample(credmark.model.Model):

#     """
#     This example returns the timestamp of the block that is contextualized.
#     """

#     def run(self, input) -> dict:

#         return {
#             "blockNumber": BlockNumber(context=self.context, sample_timestamp=1642222030)
#         }
