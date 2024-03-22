from pyhap.accessory import Accessory
from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_DOOR_LOCK
import signal
from doorlock import Doorlock
from datetime import datetime, timedelta
import os

doorlock = Doorlock(os.environ["ID"], os.environ["PASSWORD"])
login = doorlock.login()

info = doorlock.get_user_info()
target = info["memberDeviceVOList"][0]


class DoorLockAccessory(Accessory):
    category = CATEGORY_DOOR_LOCK
    block_timer = datetime.now()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        serv_door_lock = self.add_preload_service("LockMechanism")
        self.char_lock_target_state = serv_door_lock.configure_char(
            "LockTargetState", setter_callback=self.set_lock_target_state
        )
        self.char_lock_current_state = serv_door_lock.configure_char("LockCurrentState")
        self.char_lock_target_state.set_value(0)
        self.char_lock_current_state.set_value(0)

    def set_lock_target_state(self, value):
        self.block_timer = datetime.now() + timedelta(seconds=3)

        if value == 1:
            self.char_lock_target_state.set_value(1)
            doorlock.open_door(target["deviceId"], open=False)
            self.char_lock_current_state.set_value(1)

        else:
            self.char_lock_target_state.set_value(0)
            doorlock.open_door(target["deviceId"], open=True)
            self.char_lock_current_state.set_value(0)

        print(self.char_lock_current_state.get_value())

    @Accessory.run_at_interval(1)
    def run(self):
        if datetime.now() < self.block_timer:
            return
        status = doorlock.get_status(0)["locked"]

        if status != self.char_lock_current_state.get_value():
            self.char_lock_target_state.set_value(status)
            self.char_lock_current_state.set_value(status)


if __name__ == "__main__":
    driver = AccessoryDriver(
        address="0.0.0.0",
        port=int(os.environ.get("PORT", 51826)),
        persist_file="./home.state",
    )
    driver.add_accessory(accessory=DoorLockAccessory(driver, "도어락"))
    signal.signal(signal.SIGTERM, driver.signal_handler)
    driver.start()
