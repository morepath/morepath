import morepath


def main():
    config = morepath.setup()
    config.scan()
    config.commit()
