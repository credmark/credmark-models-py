
@Model.describe(slug='console.token-total-supply',
                version='1.0',
                input=Token,
                output=dict)
class ConsoleTokenSupply(Model):
    def run(self, input: Token) -> dict:
        return {'total_supply': input.token.scaled(input.token.total_supply)}
