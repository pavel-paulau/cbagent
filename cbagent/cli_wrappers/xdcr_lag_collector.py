from cbagent.collectors import XdcrLag
from cbagent.settings import Settings


def main():
    settings = Settings()
    settings.read_cfg()

    collector = XdcrLag(settings)
    collector.update_metadata()
    collector.collect()

if __name__ == '__main__':
    main()
