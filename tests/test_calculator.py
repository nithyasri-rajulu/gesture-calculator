import pytest
from calculator import Calculator,PinchGate,calculate
from app import key_at

@pytest.mark.parametrize('source,result',[('12+8','20'),('2*(3+4)','14'),('-3+5','2'),('1/4','0.25'),('1.5*2','3')])
def test_arithmetic(source,result):assert calculate(source)==result
@pytest.mark.parametrize('source',['__import__("os")','2**40','[1]','True','1e99','1/0',''])
def test_invalid(source):
    with pytest.raises((ValueError,SyntaxError,ZeroDivisionError)):calculate(source)
def test_state_edit_and_recovery():
    c=Calculator()
    for k in ['1','/','0','=']:c.press(k)
    assert c.error
    c.press('DEL');c.press('2');c.press('=');assert c.expression=='0.5' and not c.error
    c.press('8');assert c.expression=='8'
def test_hold_release_and_lost_tracking():
    g=PinchGate();assert g.update('1',.9,0) is None
    assert g.update('1',.2,.2)=='1'
    assert g.update('1',.2,1) is None
    g.update(None,None,1.1)
    assert g.update('1',.2,1.4) is None
    g.update('1',.9,1.5);assert g.update('1',.2,1.7)=='1'
def test_slide_while_pinched_does_not_press():
    g=PinchGate();g.update(None,.9,0);g.update(None,.2,.2)
    assert g.update('1',.2,.4) is None
    assert g.update('1',.2,.8) is None
def test_outside_and_gap_are_not_keys():
    assert key_at(5,5) is None
    assert key_at(919,230) is None
