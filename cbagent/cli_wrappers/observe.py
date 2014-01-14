from cbagent.collectors import ObserveLatency
from cbagent.settings import Settings


def main():
    settings = Settings()
    settings.read_cfg()

    collector = ObserveLatency(settings)
    collector.update_metadata()
    collector.collect()

if __name__ == '__main__':
    main()
