class Gun:

    def __init__(self, WT: float, MIN_CT: int, MAX_CT: int, AMMO_AMOUNT: int, TAP: bool, VIEW_ANGLES: list[list[float]], NAME: str):
        self.WT: float = WT
        self.MIN_CT: int = MIN_CT
        self.MAX_CT: int = MAX_CT
        self.AMMO_AMOUNT: int = AMMO_AMOUNT
        self.TAP: bool = TAP
        self.VIEW_ANGLES: list[list[float]] = VIEW_ANGLES
        self.NAME: str = NAME
