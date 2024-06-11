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
    const [heaterWebsocket, setheaterWebsocket] = useState(null);
    const heaterServerURL = `http://${serverInfo.heaterserver[1].ip}:${serverInfo.heaterserver[1].portHTTP}`;

    const [isRampToSetPoint, setIsRampToSetPoint] = useState(false);
    const [stayAheadValue, setStayAheadValue] = useState(0.5);
    const [rampSetPointValue, setRampSetPointValue] = useState(20);
    const heaterObjectiveTemperatureByRef = useRef(heater.objectiveTemperature);
    const isRampWorking = useRef(false);



    // useeffect to update the set point

    useEffect(() => {
        heaterObjectiveTemperatureByRef.current = heater.objectiveTemperature;
    }, [heater.objectiveTemperature]);


    const toggle = () => {
        setHeater(prev => ({ ...prev, isCollapsed: !prev.isCollapsed }));
    };

    const handleUpdateClick = () => {

        // check the if the set point is a valid number
        if (isNaN(heater.setPointSetAt)) {
            showToast('Set Point should be a valid number', 'error');
            return;
        }

        // check for min max values
        if (heater.setPointSetAt < heater.minSetPoint || heater.setPointSetAt > heater.maxSetPoint) {
            showToast(`Set Point should be between ${heater.minSetPoint} and ${heater.maxSetPoint}`, 'error');
            return;
        }

        // post temperature in json to 10.0.63.153:4031/set_temperature
        axios.post(`${heaterServerURL}/set_temperature`, {
            temperature: heater.setPointSetAt
        })
            .then((response) => {
                showToast('Set Point Updated Successfully', 'success');
            })
            .catch((error) => {
                showToast('Failed to update Set Point', 'error');
            });

    }

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


        const connectToWebSocketForTrackDetails = () => {
            if (heaterWebsocket) {
                return;
            }

            const ws = new WebSocket(`ws://${serverInfo.heaterserver[1].ip}:${serverInfo.heaterserver[1].portWS}/ws`);
            console.log("Trying to connect to websocket: Objective Heater")
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                setHeater(prev => ({
                    ...prev,
                    setPoint: data.set_point,
                    objectiveTemperature: data.objective_temperature,
                    lastUpdated: new Date().toLocaleTimeString(),
                    // timeSeriesSetPoints : data.time_series_set_points,
                    // timeSeriesObjectiveTemperatures : data.time_series_objective_temperatures,
                    // timeSeriesTimes : data.time_series_times
                }));
            };

            ws.onopen = () => {
                console.log(`Connected to objective heater server`);
            };
            ws.onerror = (error) => console.error('WebSocket error track server:', error);
            ws.onclose = () => {
                setHeater(prev => ({ ...prev, isOnline: false }));
                setheaterWebsocket(null);
                console.log(`Disconnected from objective heater server`);
                setTimeout(() => connectToWebSocketForTrackDetails(), 1000);
            };

            setheaterWebsocket(ws);
        };

        connectToWebSocketForTrackDetails();


    }, []);


    useEffect(() => {

        const intervalId = setInterval(() =>
            axios.get(`${heaterServerURL}/heartbeat`)
                .then(() => {
                    setHeater(prev => ({ ...prev, isOnline: true }));
                })
                .catch(() => {
                    setHeater(prev => ({ ...prev, isOnline: false }));
                })
            , 1000);

        return () => clearInterval(intervalId);

    }, []);




    useEffect(() => {

        const job = () => {


            if (!isRampToSetPoint) {
                isRampWorking.current = false;
                return;
            }

            if (!heater.isOnline) {
                isRampWorking.current = false;
                return;
            }


            if (heaterObjectiveTemperatureByRef.current - rampSetPointValue < -0.1){
                const newTemp = Math.min(rampSetPointValue, heaterObjectiveTemperatureByRef.current + stayAheadValue);
                setHeater(prev => ({ ...prev, setPointSetAt: newTemp }));
                

                axios.post(`${heaterServerURL}/set_temperature`, {
                    temperature: newTemp
                })
                    .then((response) => {
                        isRampWorking.current = true;
                    })
                    .catch((error) => {
                        isRampWorking.current = false;
                    });
            }
            else if (heaterObjectiveTemperatureByRef.current - rampSetPointValue >  0.1) {
                const newTemp = Math.max(rampSetPointValue, heaterObjectiveTemperatureByRef.current - stayAheadValue);
                setHeater(prev => ({ ...prev, setPointSetAt: newTemp }));

                axios.post(`${heaterServerURL}/set_temperature`, {
                    temperature: newTemp
                })
                    .then((response) => {
                        isRampWorking.current = true;
                    })
                    .catch((error) => {
                        isRampWorking.current = false;
                    });
            }
            else{
                showToast('Ramp to Set Point Completed', 'success');
                isRampWorking.current = false;
                setIsRampToSetPoint(false);
            }

        };

        const intervalId = setInterval(() => {
            job();
        }, 1000);

        return () => clearInterval(intervalId);
    }, [isRampToSetPoint]);



    return (
        <div>
            <div onClick={toggle} style={{ backgroundColor: "white", display: 'flex', justifyContent: 'space-between', borderTopLeftRadius: '10px', borderTopRightRadius: '10px', borderBottomLeftRadius: '0px', borderBottomRightRadius: '0px' }}>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <div className='fs-5 fw-bold' style={{ margin: '0px', padding: '10px', color: "black" }}>
                        Objective Heater
                    </div>

                    <div style={{
                        height: '10px',
                        width: '10px',
                        backgroundColor: heater.isOnline ? 'green' : 'red',
                        borderRadius: '50%',
                        display: 'inline-block',
                        marginLeft: '5px'
                    }}>
                    </div>
                </div>

                <div className='fs-5 fw-bold' style={{ marginLeft: 'auto', padding: '10px', color: "black" }}>
                    <FontAwesomeIcon icon={heater.isCollapsed ? faChevronUp : faChevronDown} />
                </div>
            </div>
            <Collapse isOpen={heater.isCollapsed}>
                <Card style={{ borderBottomLeftRadius: '10px', borderBottomRightRadius: '10px', borderTopLeftRadius: '0px', borderTopRightRadius: '0px' }}>
                    <CardBody>
                        <p className='fs-6 fw-bold mb-2'>
                            Last Update:
                            <span style={{ color: (heater.isOnline && heater.lastUpdated >= 0) ? 'green' : 'gray' }}>
                                {heater.lastUpdated != null ? ` ${heater.lastUpdated}` : ' NA'}
                            </span>
                        </p>

                        <p className='fs-6 fw-bold mb-2'>
                            Objective Temperature:
                            <span style={{ color: (heater.isOnline && heater.objectiveTemperature >= 0) ? 'green' : 'gray' }}>
                                {heater.objectiveTemperature >= 0 ? ` ${heater.objectiveTemperature.toFixed(1)}` : ' NA'}
                            </span>
                        </p>
                        <p className='fs-6 fw-bold mb-3'>
                            Set Point:
                            <span style={{ color: (heater.isOnline && heater.setPoint >= 0) ? 'green' : 'gray' }}>
                                {heater.setPoint >= 0 ? ` ${heater.setPoint.toFixed(1)} ` : ' NA'}
                            </span>
                        </p>
                        <div className="row">
                            <label className="form-label col-sm-6 mb-4 fs-6 fw-bold">
                                Set Current Set Point:
                            </label>
                            <div className="col-sm-6">
                                <Input type="number" step="0.1" value={heater.setPointSetAt} onChange={(event) => setHeater(prev => ({ ...prev, setPointSetAt: parseFloat(event.target.value).toFixed(1) }))} className="form-control" />
                            </div>
                        </div>


                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                            <Button color="primary" onClick={handleUpdateClick} className="btn" style={{ flex: '0 0 47%' }}>
                                Update Set Point
                            </Button>

                            <div style={{ flex: '0 0 20%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                                {
                                    heater.isOnline && Math.abs(heater.setPoint - heater.objectiveTemperature) > 0.14 &&
                                    <Spinner animation="border" role="status" style={{ width: '2rem', height: '2rem', color: heater.setPoint > heater.objectiveTemperature ? 'orange' : 'blue' }}>
                                        <span className="sr-only">Loading...</span>
                                    </Spinner>
                                }
                            </div>

                        </div>

                        <div className="row mt-3 mb-3">
                            <div className="col-sm-6 fw-bold">
                                <label for="temperature">Ramp to Temperature</label>
                                <Input
                                    id="temperature"
                                    type="number"
                                    className="form-control"
                                    placeholder='Temperature'
                                    step="0.1"
                                    value={rampSetPointValue}
                                    onChange={(event) => setRampSetPointValue(parseFloat(event.target.value))}
                                />
                            </div>
                            <div className="col-sm-6 fw-bold">
                                <label for="rate">Stay Ahead</label>
                                <Input
                                    id="stayaheadvalue"

                                    className="form-control"
                                    placeholder='Rate'
                                    type="number"
                                    step="0.05"
                                    value={stayAheadValue}
                                    onChange={(event) => setStayAheadValue(parseFloat(event.target.value))}
                                />
                            </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                            <Button
                            
                                onClick={() => setIsRampToSetPoint(!isRampToSetPoint)}
                                className= {isRampToSetPoint ? "btn btn-danger" : "btn btn-primary"}
                                style={{ flex: '0 0 47%' }}
                            >
                                {isRampToSetPoint ? "Stop Ramp" : "Ramp to"}
                            </Button>

                            <div style={{ flex: '0 0 20%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                                {
                                    heater.isOnline && isRampWorking.current &&
                                    <Spinner
                                        animation="border"
                                        role="status"
                                        style={{ width: '2rem', height: '2rem', color: heater.setPoint > heater.objectiveTemperature ? 'orange' : 'blue' }}
                                    >
                                        <span className="sr-only">Loading...</span>
                                    </Spinner>
                                }
                            </div>
                        </div>

                        {/* <img
                            src={`http://10.0.63.153:4031/plot?${imageKey}`}
                            alt="Plot"
                            style={{ width: '100%' }}
                        /> */}
                    </CardBody>
                </Card>
            </Collapse>
        </div>
    );
}

export default Heater;