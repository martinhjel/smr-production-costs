import subprocess as sp

scaling_options = ["manufacturer", "rothwell", "roulstone"]


def steigerwald():
    for opt in scaling_options:
        print(opt)
        sp.run(
            ["python", "scripts/run_mcs.py", "-p", "-s", opt],
            capture_output=True,
            text=True,
            check=True,
        )


def adjusted():
    scaling_options = ["manufacturer", "rothwell", "roulstone"]
    unit_doublings = [1,2,3,4,5]

    for opt in scaling_options:
        for unit_doubling in unit_doublings:
            print(opt, unit_doubling)
            sp.run(
                [
                    "python",
                    "scripts/run_mcs.py",
                    "-p",
                    "-s",
                    opt,
                    "-c",
                    "config/adjusted.yaml",
                    "-d",
                    "data/adjusted.yaml",
                    "-u",
                    f"{unit_doubling}"
                ],
                capture_output=True,
                text=True,
                check=True,
            )


if __name__ == "__main__":
    steigerwald()
    
    adjusted()