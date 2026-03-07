# gateway/all_tests.py

import pytest

if __name__ == '__main__':
    pytest.main(['-v', 'gateway/test_ws.py',
                 'gateway/test_base.py',
                 'gateway/test_ws_final.py',
                 'gateway/test_ws_8001.py',
                 'gateway/test_ws_2.py',
                 'gateway/test_ws_light.py'])