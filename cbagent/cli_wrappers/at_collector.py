from cbagent.collectors import ActiveTasks
from cbagent.settings import Settings


def main():
    settings = Settings()
    settings.read_cfg()

    collector = ActiveTasks(settings)
    collector.update_metadata()
    collector.collect()

if __name__ == '__main__':
    main()
