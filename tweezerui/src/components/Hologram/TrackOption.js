import React, { useState, useEffect } from 'react';
import { Collapse, CardBody, Card } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronDown, faChevronUp } from '@fortawesome/free-solid-svg-icons';
import { Form, Button } from 'react-bootstrap';
import { useGlobalContext } from '../../GlobalContext';
import axios from 'axios';

function TrackBar() {


    const { serverInfo, trackOptions, setTrackOptions, canvasRefs, drawProps, trackOptionsMinMaxVals } = useGlobalContext();

    
    const [locateWebsocket, setLocateWebsocket] = useState(null);

    const trackServerUrl = `http://${serverInfo.trackserver[1].ip}:${serverInfo.trackserver[1].portHTTP}`;

    const toggle = () => {
        setTrackOptions(prev => ({ ...prev, isOpenTrackOption: !prev.isOpenTrackOption }));
    };

    const handleChange = (event) => {
        let { name, value } = event.target;
        
        // apply the min and max values for the track options
        // first compare to float and compare
        value = parseFloat(value);
        if (value < trackOptionsMinMaxVals[name].min) {
            value = trackOptionsMinMaxVals[name].min;
        } else if (value > trackOptionsMinMaxVals[name].max) {
            value = trackOptionsMinMaxVals[name].max;
        }
        

        if (name === 'diameter' || name === 'llong') {

            let previousValue = trackOptions[name];
            let delta = parseInt(value) - previousValue;

            if (parseInt(value)  < 0) {
                setTrackOptions(prev => ({ ...prev, [name]: 0 })); 
            }
            if (value % 2 === 0) {
                
                setTrackOptions(prev => ({ ...prev, [name]: parseInt(value) +  delta/Math.abs(delta) })); 
                return
            }
        }
        
        setTrackOptions(prev => ({ ...prev, [name]: value }));


    };

    // useEffect to send ping to trackserver/heartbeat to check if trackserver is online
    // if trackserver is online, set isOnline to true

    useEffect(() => {
        
        const intervalId = setInterval(() =>
            axios.get(`${trackServerUrl}/heartbeat`)
                .then(() => {
                    setTrackOptions(prev => ({ ...prev, isOnline: true }));
                })
                .catch(() => {
                    setTrackOptions(prev => ({ ...prev, isOnline: false }));
                })
            , 1000);

        return () => clearInterval(intervalId);

    }, []);


    useEffect(() => {
        const data = {
            diameter: parseInt(trackOptions.diameter),
            separation: parseInt(trackOptions.seperation),
            percentile: parseFloat(trackOptions.percentile),
            minmass: parseInt(trackOptions.minmass),
            maxmass: parseInt(trackOptions.maxmass),
            pixelthresh: parseInt(trackOptions.pixelThresh),
            preprocess: Boolean(trackOptions.preprocess),
            lshort: parseInt(trackOptions.lshort),
            llong: parseInt(trackOptions.llong),
            min_ecc: parseFloat(trackOptions.minEcc),
            max_ecc: parseFloat(trackOptions.maxEcc),
            refine: parseInt(trackOptions.refine),
            grid_x: parseInt(trackOptions.gridX),
            grid_y: parseInt(trackOptions.gridY),
            overlap: parseInt(trackOptions.overlap)
        };

        axios.post(`${trackServerUrl}/set_track_params`, data)
            .then(response => {
                console.log(response);
            })
            .catch(error => {
                console.log(error);
            });

    }, [trackOptions.diameter,
        trackOptions.seperation,
        trackOptions.percentile,
        trackOptions.minmass,
        trackOptions.maxmass,
        trackOptions.pixelThresh,
        trackOptions.preprocess,
        trackOptions.lshort,
        trackOptions.llong,
        trackOptions.minEcc,
        trackOptions.maxEcc,
        trackOptions.refine,
        trackOptions.gridX,
        trackOptions.gridY,
        trackOptions.overlap,


    ]);

    useEffect(() => {
        if (trackOptions.receiveStream) {

            // return if already connected to websocket
            if (locateWebsocket) {
                return;
            }

            const connectToWebSocketForTrackDetails = () => {
                const ws = new WebSocket("ws://10.0.63.153:4012/ws");
                ws.onmessage = (event) => {
                    // the data has x and y which are arrays of x and y coordinates of the particles
                    // show the particles on the canvasRefs[3] as a scatter plot
                    const data = JSON.parse(event.data);
                    const x = data.x;
                    const y = data.y;

                    const ctx = canvasRefs[3].current.getContext('2d');
                    ctx.clearRect(0, 0, canvasRefs[3].current.width, canvasRefs[3].current.height);
                    ctx.fillStyle = 'red';
                    const scale = drawProps.scale;
                    for (let i = 0; i < x.length; i++) {
                        ctx.beginPath();
                        ctx.arc(x[i]*scale, y[i]*scale, 2, 0, 2 * Math.PI);
                            
                          
                        ctx.fill();
                    }

                    
                };

                ws.onopen = () => console.log(`Connected to Track Server`);
                ws.onerror = (error) => console.error('WebSocket error track server:', error);
                ws.onclose = () => {
                    console.log(`Disconnected from Track Server`);
                };

                setLocateWebsocket(ws);
            };

            connectToWebSocketForTrackDetails();
        } else {
            if (locateWebsocket) {
                locateWebsocket.close();
                setLocateWebsocket(null);
            }
        }

        return () => {
            if (locateWebsocket) {
                locateWebsocket.close();
            }
        };
    }, [trackOptions.receiveStream]);






    return (
        <div>
            <div onClick={toggle} style={{ backgroundColor: "white", display: 'flex', justifyContent: 'space-between', borderTopLeftRadius: '10px', borderTopRightRadius: '10px', borderBottomLeftRadius: '0px', borderBottomRightRadius: '0px' }}>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <div className='fs-5 fw-bold' style={{ margin: '0px', padding: '10px', color: "black" }}>
                        Track Option
                    </div>

                    <div style={{
                        height: '10px',
                        width: '10px',
                        backgroundColor: trackOptions.isOnline ? 'green' : 'red',
                        borderRadius: '50%',
                        display: 'inline-block',
                        marginLeft: '5px'
                    }}>
                    </div>
                </div>

                <div className='fs-5 fw-bold' style={{ marginLeft: 'auto', padding: '10px', color: "black" }}>
                    <FontAwesomeIcon icon={trackOptions.isOpenTrackOption ? faChevronUp : faChevronDown} />
                </div>
            </div>
            <Collapse isOpen={trackOptions.isOpenTrackOption}>
                <Card style={{ borderBottomLeftRadius: '10px', borderBottomRightRadius: '10px', borderTopLeftRadius: '0px', borderTopRightRadius: '0px' }}>
                    <CardBody>
                        <div className="d-flex align-items-center">
                            <span className="me-3 fs-6 fw-bold" style={{ color: "black" }}>Recieve Stream</span>
                            <div className="form-check form-switch fs-5">
                                <input
                                    disabled={!trackOptions.isOnline}
                                    className="form-check-input"
                                    type="checkbox"
                                    role="switch"
                                    checked={trackOptions.receiveStream}
                                    onChange={(e) => setTrackOptions(prev => ({ ...prev, receiveStream: e.target.checked }))}
                                />
                            </div>
                        </div>

                        <Form.Group className="mb-3 row fs-6 fw-bold">
                            <div className="col">
                                <Form.Label>Diameter</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="diameter"
                                    type="number"
                                    value={trackOptions.diameter}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="col">
                                <Form.Label>Seperation</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="seperation"
                                    type="number"
                                    value={trackOptions.seperation}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="col">
                                <Form.Label>Percentile</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="percentile"
                                    type="number"
                                    step="0.1"
                                    value={trackOptions.percentile}
                                    onChange={handleChange}
                                />
                            </div>
                        </Form.Group>

                        <Form.Group className="mb-3 row fs-6 fw-bold">
                            <div className="col">
                                <Form.Label>Minmass</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="minmass"
                                    type="number"
                                    value={trackOptions.minmass}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="col">
                                <Form.Label>Maxmass</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="maxmass"
                                    type="number"
                                    value={trackOptions.maxmass}
                                    style={{ backgroundColor: (!trackOptions.isOnline || trackOptions.maxmass >= 0) ? '' : 'lightgray' }}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="col">
                                <Form.Label>PixelThresh</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="pixelThresh"
                                    type="number"
                                    style={{ backgroundColor: (!trackOptions.isOnline || trackOptions.pixelThresh >= 0) ? '' : 'lightgray' }}
                                    value={trackOptions.pixelThresh}
                                    onChange={handleChange}
                                />
                            </div>
                        </Form.Group>

                        <Form.Group className="mb-3 row fs-6 fw-bold">

                            <div className="col">
                                <Form.Label>Preprocess</Form.Label>
                                <Form.Control
                                    as="select"
                                    disabled={!trackOptions.isOnline}
                                    name="preprocess"
                                    value={trackOptions.preprocess}
                                    onChange={e => setTrackOptions(prev => ({ ...prev, preprocess: e.target.value == 'true' }))}
                                >
                                    <option value={true}>Yes</option>
                                    <option value={false}>No</option>
                                </Form.Control>
                            </div>


                            <div className="col">
                                <Form.Label>Lshort</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="lshort"
                                    type="number"
                                    style={{ backgroundColor: (!trackOptions.isOnline || trackOptions.preprocess) ? '' : 'lightgray' }}

                                    value={trackOptions.lshort}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="col">
                                <Form.Label>LLong</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="llong"
                                    type="number"
                                    style={{ backgroundColor: (!trackOptions.isOnline || trackOptions.preprocess) ? '' : 'lightgray' }}
                                    value={trackOptions.llong}
                                    onChange={handleChange}
                                />
                            </div>

                        </Form.Group>


                        <Form.Group className="mb-3 row fs-6 fw-bold">
                            <div className="col">
                                <Form.Label>Min Ecc</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="minEcc"
                                    type="number"
                                    step="0.01"
                                    value={trackOptions.minEcc}
                                    style={{ backgroundColor: (!trackOptions.isOnline || trackOptions.minEcc >= 0) ? '' : 'lightgray' }}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="col">
                                <Form.Label>Max Ecc</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="maxEcc"
                                    type="number"
                                    step="0.01"
                                    value={trackOptions.maxEcc}
                                    style={{ backgroundColor: (!trackOptions.isOnline || trackOptions.maxEcc >= 0) ? '' : 'lightgray' }}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="col">
                                <Form.Label>Refine</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="refine"
                                    type="number"
                                    value={trackOptions.refine}
                                    onChange={handleChange}
                                />
                            </div>
                        </Form.Group>

                        <Form.Group className="mb-3 row fs-6 fw-bold">
                            <div className="col">
                                <Form.Label>Grid X</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="gridX"
                                    type="number"
                                    step="25"
                                    min="200"
                                    max="1000"
                                    value={trackOptions.gridX}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="col">
                                <Form.Label>Grid Y</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="gridY"
                                    type="number"
                                    min="200"
                                    step="25"
                                    max="1000"
                                    value={trackOptions.gridY}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="col">
                                <Form.Label>Overlap</Form.Label>
                                <Form.Control
                                    disabled={!trackOptions.isOnline}
                                    name="overlap"
                                    type="number"
                                    min="20"
                                    step="5"
                                    max="200"
                                    value={trackOptions.overlap}
                                    onChange={handleChange}
                                />
                            </div>
                        </Form.Group>


                    </CardBody>
                </Card>
            </Collapse>
        </div>
    );
}

export default TrackBar;