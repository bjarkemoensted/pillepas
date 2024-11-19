import copy
import json
import os
import pathlib
import platformdirs
import warnings

from pillepas.automation.robots import FormBot


def fill(data: dict, auto_submit=False):
    robot = FormBot(verbose=True, target_form_data=d)
    robot.loop_form(try_click_next=True)
    
    if auto_submit:
        robot.click_final_submit_button()
    
    res = robot.wrap_up()
    return res


if __name__ == '__main__':
    import pathlib
    from pprint import pprint
    import json
    
    d = json.loads((pathlib.Path(__file__).parent.parent.parent.parent / "deleteme_recorded.json").read_text())
    del d["FormId"]
    
    res = fill(data=d, auto_submit=False)
    pprint(res)
    