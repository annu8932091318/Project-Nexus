from src.factory import NexusFactory


def run_nexus_factory(prompt: str):
    factory = NexusFactory()
    return factory.run_build(prompt)


if __name__ == "__main__":
    print("--- Project Nexus Local AI Factory ---")
    user_prompt = input("What would you like me to build? ")
    result = run_nexus_factory(user_prompt)
    print(result)
