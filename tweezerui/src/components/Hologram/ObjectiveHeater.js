import React, { useState, useEffect, useRef } from 'react';
import { Collapse, CardBody, Card, CardTitle, Input } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronDown, faChevronUp } from '@fortawesome/free-solid-svg-icons';
import { Form, Button } from 'react-bootstrap';
import { useGlobalContext } from '../../GlobalContext';
import axios from 'axios';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { Slide } from 'react-toastify';
import Spinner from 'react-bootstrap/Spinner'; // or from 'react-spinners';

function Heater() {
    const { serverInfo, heater, setHeater } = useGlobalContext();
    const [heaterWebsocket, setHeaterWebsocket] = useState(null);
    const heaterServerURL = `http://${serverInfo.heaterserver[1].ip}:${serverInfo.heaterserver[1].portHTTP}`;

    const [isRampToSetPoint, setIsRampToSetPoint] = useState(false);
    const [stayAheadValue, setStayAheadValue] = useState(0.5);
    const [rampSetPointValue, setRampSetPointValue] = useState(20);
    const [useChiller, setUseChiller] = useState(false);
    const [flowBtnEnabled, setFlowBtnEnabled] = useState(true);
    const heaterObjectiveTemperatureByRef = useRef(heater.objectiveTemperature);
    const isRampWorking = useRef(false);
    const isRampCleanUpPending = useRef(false);

    const [chillerFlow, setChillerFlow] = useState(false);

    const heaterError = useRef(false);



    useEffect(() => {
        heaterObjectiveTemperatureByRef.current = heater.objectiveTemperature;
    }, [heater.objectiveTemperature]);

    const toggle = () => {
        setHeater(prev => ({ ...prev, isCollapsed: !prev.isCollapsed }));
    };

    const handleUpdateClick = () => {
        if (isNaN(heater.setPointSetAt)) {
            showToast('Set Point should be a valid number', 'error');
            return;
        }

        if (heater.setPointSetAt < heater.minSetPoint || heater.setPointSetAt > heater.maxSetPoint) {
            showToast(`Set Point should be between ${heater.minSetPoint} and ${heater.maxSetPoint}`, 'error');
            return;
        }

        axios.post(`${heaterServerURL}/heater/set_temperature`, { temperature: heater.setPointSetAt })
            .then((response) => {
                showToast('Set Point Updated Successfully', 'success');
            })
            .catch((error) => {
                showToast('Failed to update Set Point', 'error');
            });
    };

    const handleChillerUpdateClick = () => {
        if (isNaN(heater.chillerSetPointAt)) {
            showToast('Chiller Set Point should be a valid number', 'error');
            return;
        }

        axios.post(`${heaterServerURL}/chiller/set_temperature`, { temperature: heater.chillerSetPointAt })
            .then((response) => {
                showToast('Chiller Set Point Updated Successfully', 'success');
            })
            .catch((error) => {
                showToast('Failed to update Chiller Set Point', 'error');
            });
    };


    useEffect(() => {

        setFlowBtnEnabled(false);

        let showSucess = chillerFlow != heater.chillerIsFlowing
        if (heater.chillerIsFlowing == undefined)
            showSucess = false;




        axios.post(`${heaterServerURL}/chiller/set_flow`, { flow: chillerFlow })
            .then((response) => {
                setFlowBtnEnabled(true);
                setHeater(prev => ({ ...prev, chillerFlow: chillerFlow }));
                // flow turned on/off successfully
                if (showSucess)
                    showToast(`Chiller Flow ${chillerFlow ? 'On' : 'Off'}`, 'success');

            })
            .catch((error) => {
                setFlowBtnEnabled(true);
                showToast('Failed to use chiller', 'error');
            });


    }, [chillerFlow]);

    const showToast = (msg, type, delay = 2000) => {
        toast[type](msg, {
            position: "bottom-right",
            autoClose: delay,
            hideProgressBar: false,
            closeOnClick: true,
            pauseOnHover: true,
            draggable: true,
            progress: undefined,
            theme: "dark",
            transition: Slide,
        });
    };

    useEffect(() => {
        const connectToWebSocket = () => {
            if (heaterWebsocket) return;

            const ws = new WebSocket(`ws://${serverInfo.heaterserver[1].ip}:${serverInfo.heaterserver[1].portWS}/ws`);
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.connection_error) {
                    // showToast('Temperature server error', data.connection_error_msg)
                    showToast(data.connection_error_msg, 'error')



                }

                setHeater(prev => ({
                    ...prev,
                    setPoint: data.heater_set_point,
                    objectiveTemperature: data.heater_objective_temperature,
                    lastUpdated: new Date().toLocaleTimeString(),
                    chillerSetPoint: data.chiller_set_point,
                    chillerTemperature: data.chiller_liquid_temperature,
                    chillerIsFlowing: data.chiller_flow,

                }));
            };

            ws.onopen = () => console.log(`Connected to server`);
            ws.onerror = (error) => console.error('WebSocket error server:', error);
            ws.onclose = () => {
                setHeater(prev => ({ ...prev, isOnline: false }));
                setHeaterWebsocket(null);
                setTimeout(() => connectToWebSocket(), 1000);
            };

            setHeaterWebsocket(ws);
        };

        connectToWebSocket();
    }, []);

    useEffect(() => {
        const intervalId = setInterval(() => {
            axios.get(`${heaterServerURL}/heartbeat`)
                .then(() => setHeater(prev => ({ ...prev, isOnline: true })))
                .catch(() => setHeater(prev => ({ ...prev, isOnline: false })));
        }, 1000);

        return () => clearInterval(intervalId);
    }, []);

    useEffect(() => {
        const job = () => {
            if (!isRampToSetPoint) {
                setChillerFlow(false);
                isRampWorking.current = false;
                if (isRampCleanUpPending.current) {
                    // set heater to objective temperature
                    axios.post(`${heaterServerURL}/heater/set_temperature`, { temperature: heaterObjectiveTemperatureByRef.current })
                        .then((response) => {
                            isRampCleanUpPending.current = false;
                            setHeater(prev => ({ ...prev, setPointSetAt: heaterObjectiveTemperatureByRef.current }));
                            showToast('Ramp cleanup done', 'success');
                        })
                        .catch((error) => {
                            showToast('Failed to perform operations for ramp cleanup', error);
                        });
                }
                return;
            }

            if (!heater.isOnline) {
                setChillerFlow(false);
                isRampWorking.current = false;
                return;
            }

            if (heaterObjectiveTemperatureByRef.current - rampSetPointValue < -0.1) {
                setUseChiller(false);
                setFlowBtnEnabled(false);
                setChillerFlow(false);
                const newTemp = Math.min(rampSetPointValue, heaterObjectiveTemperatureByRef.current + stayAheadValue);
                setHeater(prev => ({ ...prev, setPointSetAt: newTemp }));

                axios.post(`${heaterServerURL}/heater/set_temperature`, { temperature: newTemp })
                    .then((response) => {
                        isRampWorking.current = true;
                    })
                    .catch((error) => {
                        isRampWorking.current = false;
                    });

            } else if (heaterObjectiveTemperatureByRef.current - rampSetPointValue > 0.1) {
                isRampCleanUpPending.current = true;
                setFlowBtnEnabled(true);
                setChillerFlow(useChiller);
                // const newTemp = Math.max(rampSetPointValue, heaterObjectiveTemperatureByRef.current - stayAheadValue);
                const newTemp = 18;
                setHeater(prev => ({ ...prev, setPointSetAt: newTemp }));

                if (useChiller) {

                    // if flow is already on, then no need to set it again

                    axios.post(`${heaterServerURL}/chiller/set_flow`, { flow: true })
                        .then((response) => {
                            setHeater(prev => ({ ...prev, chillerFlow: true }));
                        }
                        )
                        .catch((error) => {
                            showToast('Failed to use chiller', error);
                        }
                        );
                }
                else {
                }

                axios.post(`${heaterServerURL}/heater/set_temperature`, { temperature: newTemp })
                    .then((response) => {
                        isRampWorking.current = true;
                    })
                    .catch((error) => {
                        isRampWorking.current = false;
                    });
            } else {
                showToast('Ramp to Set Point Completed', 'success');
                isRampWorking.current = false;
                setIsRampToSetPoint(false);
            }
        };

        const intervalId = setInterval(() => job(), 1000);

        return () => clearInterval(intervalId);
    }, [isRampToSetPoint, useChiller]);

    return (
        <div>
            <div onClick={toggle} style={{ backgroundColor: "white", display: 'flex', justifyContent: 'space-between', borderRadius: '10px 10px 0 0' }}>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <div className='fs-5 fw-bold' style={{ padding: '10px', color: "black" }}>
                        Objective Thermostat
                    </div>
                    <div style={{
                        height: '10px',
                        width: '10px',
                        backgroundColor: heater.isOnline ? 'green' : 'red',
                        borderRadius: '50%',
                        marginLeft: '5px'
                    }}></div>
                </div>
                <div className='fs-5 fw-bold' style={{ padding: '10px', color: "black" }}>
                    <FontAwesomeIcon icon={heater.isCollapsed ? faChevronUp : faChevronDown} />
                </div>
            </div>
            <Collapse isOpen={heater.isCollapsed}>
                <Card style={{ borderRadius: '0 0 10px 10px' }}>
                    <div className='d-flex justify-content-center align-items-center'>
                        <div className='fs-6 fw-bold mt-1'>
                            Last Update: <span style={{ color: heater.isOnline ? 'green' : 'gray' }}>{heater.lastUpdated || 'NA'}</span>
                        </div>
                    </div>

                    <CardBody>
                        <CardTitle className='fs-5 fw-bold mb-3' style={{ color: 'red' }}>Objective Heater</CardTitle>

                        <p className='fs-6 fw-bold mb-2'>
                            Objective Temperature: <span style={{ color: heater.isOnline ? 'green' : 'gray' }}>{heater.objectiveTemperature?.toFixed(1) || ' NA'}</span>
                        </p>
                        <p className='fs-6 fw-bold mb-3'>
                            Set Point: <span style={{ color: heater.isOnline ? 'green' : 'gray' }}>{heater.setPoint?.toFixed(1) || ' NA'}</span>
                        </p>
                        <div className="row">
                            <label className="form-label col-sm-6 mb-4 fs-6 fw-bold">Set Point:</label>
                            <div className="col-sm-6">
                                <Input type='number' step="0.1" value={heater.setPointSetAt} onChange={(event) => setHeater(prev => ({ ...prev, setPointSetAt: parseFloat(event.target.value).toFixed(1) }))} className="form-control" />
                            </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                            <Button onClick={handleUpdateClick} className="btn btn-danger" style={{ flex: '0 0 47%' }}>Update Set Point</Button>
                            <div style={{ flex: '0 0 20%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                                {heater.isOnline && Math.abs(heater.setPoint - heater.objectiveTemperature) > 0.14 && (
                                    <Spinner animation="border" role="status" style={{ width: '2rem', height: '2rem', color: heater.setPoint > heater.objectiveTemperature ? 'orange' : 'blue' }}>
                                        <span className="sr-only">Loading...</span>
                                    </Spinner>
                                )}
                            </div>
                        </div>

                        <hr />
                        <CardTitle className='fs-5 fw-bold mb-3' style={{ color: 'blue' }}>Objective Chiller</CardTitle>
                        <p className='fs-6 fw-bold mb-2'>
                            Chiller temperature: <span style={{ color: heater.isOnline ? 'green' : 'gray' }}>{heater.chillerTemperature?.toFixed(1) || ' NA'}</span>
                        </p>
                        <p className='fs-6 fw-bold mb-2'>
                            Set Point: <span style={{ color: heater.isOnline ? 'green' : 'gray' }}>{heater.chillerSetPoint?.toFixed(1) || ' NA'}</span>
                        </p>
                        <p className='fs-6 fw-bold mb-2'>
                            Flow: <span style={{ color: heater.isOnline ? 'green' : 'gray' }}>{heater.chillerIsFlowing ? 'On' : 'Off'}</span>
                        </p>
                        <div className="row">
                            <label className="form-label col-sm-6 mb-4 fs-6 fw-bold">Set Point:</label>
                            <div className="col-sm-6">
                                <Input type="number" step="0.1" value={heater.chillerSetPointAt} onChange={(event) => setHeater(prev => ({ ...prev, chillerSetPointAt: parseFloat(event.target.value).toFixed(1) }))} className="form-control" />
                            </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                            <Button onClick={handleChillerUpdateClick} className="btn" style={{ flex: '0 0 47%' }}>Update Set Point</Button>

                            {/* <div style={{ flex: '0 0 47%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <label htmlFor="chillerFlowToggle" className="fw-bold me-2">Flow</label>
                                <div className="form-check form-switch">
                                    <input
                                        className="form-check-input"
                                        type="checkbox"
                                        id="chillerFlowToggle"
                                        checked={chillerFlow}
                                        disabled={!flowBtnEnabled}
                                        onChange={() => setChillerFlow(!chillerFlow)}
                                    />
                                </div>
                            </div> */}

                            <div style={{ flex: '0 0 20%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                                {heater.isOnline && Math.abs(heater.chillerSetPoint - heater.chillerObjectiveTemperature) > 0.14 && (
                                    <Spinner animation="border" role="status" style={{ width: '2rem', height: '2rem', color: heater.chillerSetPoint > heater.chillerObjectiveTemperature ? 'orange' : 'blue' }}>
                                        <span className="sr-only">Loading...</span>
                                    </Spinner>
                                )}
                            </div>
                        </div>


                        <hr></hr>

                        <CardTitle className='fs-5 fw-bold mb-3' style={{ color: 'green' }}>Thermostat</CardTitle>
                        <div className="row mt-3 mb-3">
                            <div className="col-sm-4 d-flex flex-column align-items-start">
                                <label htmlFor="temperature" className="fw-bold">Ramp to</label>
                                <input
                                    id="temperature"
                                    type="number"
                                    className="form-control"
                                    placeholder="Temperature"
                                    step="0.1"
                                    value={rampSetPointValue}
                                    onChange={(event) => setRampSetPointValue(parseFloat(event.target.value))}
                                />
                            </div>

                            <div className="col-sm-4 d-flex flex-column align-items-start">
                                <label htmlFor="rate" className="fw-bold">Stay Ahead</label>
                                <input
                                    id="stayaheadvalue"
                                    type="number"
                                    className="form-control"
                                    placeholder="Rate"
                                    step="0.05"
                                    value={stayAheadValue}
                                    onChange={(event) => setStayAheadValue(parseFloat(event.target.value))}
                                />
                            </div>

                            <div className="col-sm-4 d-flex flex-column align-items-center">
                                <label htmlFor="useChiller" className="fw-bold">Use Chiller</label>
                                <div className="form-check form-switch w-100 mt-2 d-flex justify-content-center">
                                    <input
                                        className="form-check-input"
                                        type="checkbox"
                                        id="useChiller"
                                        checked={useChiller}
                                        onChange={(e) => setUseChiller(e.target.checked)}
                                    />
                                </div>
                            </div>
                        </div>



                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                            <Button
                                onClick={() => setIsRampToSetPoint(!isRampToSetPoint)}
                                className={isRampToSetPoint ? "btn btn-success" : "btn btn-success"}
                                style={{ flex: '0 0 47%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}
                            >
                                {isRampToSetPoint ? (
                                    <>
                                        <Spinner
                                            as="span"
                                            animation="border"
                                            size="sm"
                                            role="status"
                                            aria-hidden="true"
                                            style={{ marginRight: '5px' }}
                                        />
                                        Stop Ramp
                                    </>
                                ) : (
                                    "Ramp to"
                                )}
                            </Button>

                        </div>


                    </CardBody>
                </Card>
            </Collapse>
        </div>
    );
}

export default Heater;
