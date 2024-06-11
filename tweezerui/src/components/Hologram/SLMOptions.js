import React, { useState, useEffect, useRef } from 'react';
import { Collapse, CardBody, Card } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronDown, faChevronUp } from '@fortawesome/free-solid-svg-icons';
import { Form, Button, ButtonGroup } from 'react-bootstrap';
import { useGlobalContext } from '../../GlobalContext';

import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { Slide } from 'react-toastify';


function SLMOptions() {
    const { serverInfo, slmOptions, setSLMOptions, canvasRefs, drawProps } = useGlobalContext();
    const [receiveBackStream, setReceiveBackStream] = useState(false);
    const [lockCanvas, setLockCanvas] = useState(false);

    const mousePosition = useRef({ x: 0, y: 0 });
    const [points, setPoints] = useState({});
    const selectedPoint = useRef(null);
    const [websocket, setWebsocket] = useState(null);

    const [slmPointsData, setSlmPointsData] = useState({});



    const toggle = () => {
        setSLMOptions(prev => ({ ...prev, isCollapsed: !prev.isCollapsed }));
    };


    useEffect(() => {


        const connectToSLMServer = () => {
            const ws = new WebSocket(`ws://${serverInfo.slmserver[1].ip}:${serverInfo.slmserver[1].portWS}`);
            ws.onopen = () => {
                console.log('Connected to SLM Server');
                setSLMOptions(prev => ({ ...prev, isOnline: true }));
                setWebsocket(ws);
            }
            ws.onclose = () => {
                console.log('Disconnected from SLM Server');
                setSLMOptions(prev => ({ ...prev, isOnline: false }));

                setTimeout(() => {
                    connectToSLMServer();
                }, 1000);
            }

            ws.onmessage = (event) => {
                /* the response is like 

                {
                    "update_type": "get_points",
                    "id": "123",
                    "points": {
                        "x_array": [],
                        "y_array": [],
                        "z_array": [],
                        "intensity_array": [],
                        "data_received_time": -1
                    },
                    "affine": {
                        "last_updated": 1718098409.6141114,
                        "last_data_received": 1718098409.6011057,
                        "last_check_for_updates": 1718100211.2217202,
                        "SLM_X_0": 10,
                        "SLM_Y_0": 10,
                        "CAM_X_0": 10,
                        "CAM_Y_0": 10,
                        "SLM_X_1": -20,
                        "SLM_Y_1": -20,
                        "CAM_X_1": -20,
                        "CAM_Y_1": -20,
                        "SLM_X_2": -30,
                        "SLM_Y_2": 10,
                        "CAM_X_2": -30,
                        "CAM_Y_2": 10
                    }
                    }

                    */
                setSlmPointsData(JSON.parse(event.data));
            }
        }


        const ws = connectToSLMServer();

        return () => {
            try {
                ws.close();
            } catch (error) { }
        };

    }, []);

    const updateAffine = () => {

        /* update the affine parameters to the SLM server
        {
            "command": "update_affine",
            "id": "12345",
            "affine": {
                "SLM_X_0": 100,
                "SLM_Y_0": 100,
                "CAM_X_0": 100,
                "CAM_Y_0": 100,
                "SLM_X_1": 200,
                "SLM_Y_1": 200,
                "CAM_X_1": 200,
                "CAM_Y_1": 200,
                "SLM_X_2": 300,
                "SLM_Y_2": 300,
                "CAM_X_2": 300,
                "CAM_Y_2": 300
            }
        }
        */

        if (websocket && slmOptions.isOnline && websocket.readyState === 1) {
            const message = {
                command: "update_affine",
                id: `m1${new Date().getTime()}`,
                affine: slmOptions.affine
            };
            websocket.send(JSON.stringify(message));
        }

    };


    // on change points, message the SLM server to update the points
    useEffect(() => {
        if (websocket && slmOptions.isOnline && websocket.readyState === 1) {

            // TODO : send the points to the SLM server

            // the format is 
            /*
            {
                "command": "update_points",
                "id": "123",
                "points": {
                  "x_array": [-4.0, 4.0],
                  "y_array": [0, 0],
                  "z_array": [0.0, 0.0 ],
                  "intensity_array": [1.0, 1.0]
                }
              }
              */

            const xArray = [];
            const yArray = [];
            const zArray = [];
            const intensityArray = [];

            for (const key in points) {
                const point = points[key];
                xArray.push(point[0] * drawProps.scale);
                yArray.push(point[1] * drawProps.scale);
                zArray.push(point[2]);
                intensityArray.push(point[3]);
            }

            // id is machine_id which is m1+current time
            const id = `m1${new Date().getTime()}`;

            const message = {
                command: "update_points",
                id: id,
                points: {
                    x_array: xArray,
                    y_array: yArray,
                    z_array: zArray,
                    intensity_array: intensityArray
                }
            };
            websocket.send(JSON.stringify(message));

        }
    }, [points, websocket, slmOptions.isOnline]);



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


    const findNearestPoint = (points, x, y) => {
        let nearestPointKey = null;
        let minDistance = 9999999999;

        for (const key in points) {
            const point = points[key];
            const distance = Math.pow(point[0] - x, 2) + Math.pow(point[1] - y, 2);
            if (distance < minDistance) {
                minDistance = distance;
                nearestPointKey = key;
            }
        }

        return { nearestPointKey, minDistance };
    };


    const addPoint = (nearestPoint, x, y) => {

        // check if the nearest point is within a certain distance
        if (nearestPoint) {
            const { nearestPointKey, minDistance } = nearestPoint;
            if (minDistance < 100) {
                showToast('Cannot add | Too near to another point', 'error');
                return;
            }
        }

        const key = `${x}_${y}`;

        const newPoint = [parseFloat(x), parseFloat(y), parseFloat(slmOptions.currentZ), parseFloat(slmOptions.currentIntensity)];

        setPoints(prev => ({ ...prev, [key]: newPoint }));
    };


    const removePoint = (x, y, cutoff) => {

        const { nearestPointKey, minDistance } = findNearestPoint(points, x, y);

        if (minDistance > cutoff) {
            return;
        }
        setPoints(prev => {
            const newPoints = { ...prev };
            if (newPoints[nearestPointKey]) {

            }
            delete newPoints[nearestPointKey];
            return newPoints;
        });
    };


    const addNewFocalSpot = (x, y, z, intensity, cutoff) => {

        // find the nearest point
        const { nearestPointKey, minDistance } = findNearestPoint(points, x, y);

        if (minDistance < cutoff) {
            showToast('Cannot add | Too near to another point', 'error');
            return;
        }

        addPoint({ nearestPointKey, minDistance }, x, y);

    };



    const updatePoint = (x, y, z, intensity, id) => {
        setPoints(prev => {
            const newPoints = { ...prev };
            if (newPoints[id]) {
                newPoints[id] = [x, y, z, intensity];
            }
            return newPoints;
        });
    };

    const removeById = (id) => {
        setPoints(prev => {
            const newPoints = { ...prev };
            if (newPoints[id]) {
                delete newPoints[id];
            }
            return newPoints;
        });
    };

    useEffect(() => {
        if (receiveBackStream) {
            const interval = setInterval(() => {
                const message = {
                    "command": "get_points",
                    "id": "123",
                };

                if (websocket && slmOptions.isOnline && websocket.readyState === 1) {
                    websocket.send(JSON.stringify(message));
                }

            }, 500);

            // Clear interval on component unmount
            return () => clearInterval(interval);
        }
    }, [receiveBackStream]);

    useEffect(() => {
        const canvas = canvasRefs[4].current;

        const handleMouseMove = (event) => {
            const rect = canvas.getBoundingClientRect();
            const mouseX = Math.round(event.clientX - rect.left);
            const mouseY = Math.round(event.clientY - rect.top);

            mousePosition.current = { x: mouseX, y: mouseY };

            if (selectedPoint.current) {
                const { x, y } = mousePosition.current;
                const point = points[selectedPoint.current];
                point[0] = x;
                point[1] = y;
                setPoints(prev => ({ ...prev, [selectedPoint.current]: point }));
                // set slmOptions.focalSpot to the selected point

            }
        };

        const handleKeyPress = (event) => {
            switch (event.key.toUpperCase()) {
                case 'R':
                    removePoint(mousePosition.current.x, mousePosition.current.y, 100);
                    break;
                case 'E':
                    break;
                default:
                    break;
            }
        };

        const handleMouseDown = (event) => {




            const { x, y } = mousePosition.current;
            if (x < 0 || x > canvas.width || y < 0 || y > canvas.height) {
                return;
            }

            if (lockCanvas) {
                return;
            }


            const { nearestPointKey, minDistance } = findNearestPoint(points, x, y);
            if (minDistance > 100) {
                addPoint({ nearestPointKey, minDistance }, x, y);
            }
            else {
                // return if outside the canvas

                selectedPoint.current = nearestPointKey;
                const copyX = points[nearestPointKey][0];
                const copyY = points[nearestPointKey][1];
                const copyZ = points[nearestPointKey][2];
                const copyIntensity = points[nearestPointKey][3];
                const copyID = nearestPointKey;
                setSLMOptions(prev => ({ ...prev, focalSpot: { x: copyX, y: copyY, z: copyZ, intensity: copyIntensity, id: copyID } }));

            }

        };

        const handleMouseUp = (event) => {

            selectedPoint.current = null;
        };


        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('keypress', handleKeyPress);
        // event listener for mousedown and mouseup
        window.addEventListener('mousedown', handleMouseDown);
        window.addEventListener('mouseup', handleMouseUp);

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('keypress', handleKeyPress);
            window.removeEventListener('mousedown', handleMouseDown);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [points, canvasRefs, slmOptions]);



    const interpolateColor = (color1, color2, factor) => {
        const result = color1.slice();
        for (let i = 0; i < 3; i++) {
            result[i] = Math.round(result[i] + factor * (color2[i] - color1[i]));
        }
        return result;
    };

    const color1 = [255, 255, 0];
    const color2 = [0, 255, 255];

    useEffect(() => {

        const canvas = canvasRefs[4].current;
        const context = canvas.getContext('2d');
        context.clearRect(0, 0, canvas.width, canvas.height);
        for (const key in points) {
            // const point = points[key];
            // const color = interpolateColor(color1, color2, point[3]); // assuming point[3] is the intensity
            // context.beginPath();
            // context.arc(point[0], point[1], 5, 0, 2 * Math.PI);
            // context.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
            // context.fill();

            const point = points[key];
            const color = interpolateColor(color1, color2, point[3]); // assuming point[3] is the intensity
            context.beginPath();
            context.arc(point[0], point[1], 5, 0, 2 * Math.PI);
            context.strokeStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
            context.lineWidth = 2;
            context.stroke();

        }

        // for selected point, have a white circle around it
        if (selectedPoint.current) {
            const point = points[selectedPoint.current];
            context.beginPath();
            context.arc(point[0], point[1], 10, 0, 2 * Math.PI);
            context.strokeStyle = 'white';
            context.stroke();
        }


        if (slmPointsData.points) {
            // draw the points from the slmPointsData
            // while drawing, scale down the points
            // color --> faint orange
            const color = [160, 32, 240];

            for (let i = 0; i < slmPointsData.points.x_array.length; i++) {

                const x = slmPointsData.points.x_array[i] / drawProps.scale;
                const y = slmPointsData.points.y_array[i] / drawProps.scale;
                const z = slmPointsData.points.z_array[i];
                const intensity = slmPointsData.points.intensity_array[i];

                // draw as a plus sign
                context.beginPath();
                context.moveTo(x - 5, y);
                context.lineTo(x + 5, y);
                context.moveTo(x, y - 5);
                context.lineTo(x, y + 5);
                context.strokeStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
                context.lineWidth = 2; // Set the line width to 2
                context.stroke();


            }
        }


    }, [points, canvasRefs[4], selectedPoint.current, receiveBackStream, drawProps.scale, slmPointsData]);





    return (
        <div>

            <div onClick={toggle} style={{ backgroundColor: "white", display: 'flex', justifyContent: 'space-between', borderTopLeftRadius: '10px', borderTopRightRadius: '10px', borderBottomLeftRadius: '0px', borderBottomRightRadius: '0px' }}>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <div className='fs-5 fw-bold' style={{ margin: '0px', padding: '10px', color: "black" }}>
                        SLM Options
                    </div>

                    <div style={{
                        height: '10px',
                        width: '10px',
                        backgroundColor: slmOptions.isOnline ? 'green' : 'red',
                        borderRadius: '50%',
                        display: 'inline-block',
                        marginLeft: '5px'
                    }}>
                    </div>

                    <div style={{
                        height: '25px',
                        width: '200px',



                        marginLeft: '20px'
                    }}>
                        <p style={{
                            color: (
                                mousePosition.current.x >= 0 &&
                                mousePosition.current.x <= (canvasRefs[4]?.current?.width || 0) &&
                                mousePosition.current.y >= 0 &&
                                mousePosition.current.y <= (canvasRefs[4]?.current?.height || 0)
                            ) ? 'green' : 'gray'
                        }}>
                            ({Math.floor(mousePosition.current.x)}, {Math.floor(mousePosition.current.y)})
                        </p>

                    </div>
                </div>







                <div className='fs-5 fw-bold' style={{ marginLeft: 'auto', padding: '10px', color: "black" }}>
                    <FontAwesomeIcon icon={slmOptions.isCollapsed ? faChevronUp : faChevronDown} />
                </div>
            </div>

            <Collapse isOpen={slmOptions.isCollapsed}>
                <Card style={{ borderBottomLeftRadius: '10px', borderBottomRightRadius: '10px', borderTopLeftRadius: '0px', borderTopRightRadius: '0px' }}>
                    <CardBody>



                        <div className="d-flex justify-content-between">
                            <div className="d-flex align-items-center mb-3">
                                <span className="me-3 fs-6 fw-bold" style={{ color: "black" }}>Recieve Back Stream</span>
                                <div className="form-check form-switch fs-5">
                                    <input
                                        disabled={!slmOptions.isOnline}
                                        className="form-check-input"
                                        type="checkbox"
                                        role="switch"
                                        checked={receiveBackStream}
                                        onChange={(e) => setReceiveBackStream(e.target.checked)}
                                    />
                                </div>
                            </div>

                            <div className="d-flex align-items-center mb-3">
                                <span className="me-3 fs-6 fw-bold" style={{ color: "black" }}>Lock Canvas</span>
                                <div className="form-check form-switch fs-5">
                                    <input
                                        disabled={!slmOptions.isOnline}
                                        className="form-check-input"
                                        type="checkbox"
                                        role="switch"
                                        checked={lockCanvas}
                                        onChange={(e) => setLockCanvas(e.target.checked)}
                                    />
                                </div>
                            </div>
                        </div>

                        <div className='container mb-3'>
                            <div className="row">
                                <Form className="container">
                                    <div className="row form-group" style={{ marginBottom: '0' }}>
                                        <div className="col-md-6 fw-bold" style={{ padding: '0' }}>
                                            <label htmlFor="default_z" style={{ display: 'block', textAlign: 'center' }}>Default Z</label>
                                            <input
                                                type="number"
                                                id="default_z"
                                                className="form-control"
                                                placeholder="Default Z"
                                                style={{ margin: '0', borderRadius: '0' }}
                                                value={slmOptions.currentZ}
                                                onChange={(e) => slmOptions.currentZ = e.target.value}
                                            />
                                        </div>
                                        <div className="col-md-6 fw-bold" style={{ padding: '0' }}>
                                            <label htmlFor="default_i" style={{ display: 'block', textAlign: 'center' }}>Default Intensity</label>
                                            <input
                                                type="number"
                                                step="0.001"
                                                id="default_i"
                                                className="form-control"
                                                placeholder="Default Intensity"
                                                style={{ margin: '0', borderRadius: '0' }}
                                                value={slmOptions.currentIntensity}
                                                onChange={(e) => slmOptions.currentIntensity = e.target.value}
                                            />
                                        </div>
                                    </div>
                                </Form>

                            </div>
                        </div>

                        <h5>Focal Spot:</h5>
                        <div className='container fw-bold mb-3'>
                            <div className="row">
                                <Form className="container">
                                    <div className="row form-group" style={{ marginBottom: '0' }}>
                                        <div className="col-md-3" style={{ padding: '0' }}>
                                            <label for="x_point" style={{ display: 'block', textAlign: 'center' }}>X</label>
                                            <input
                                                type="number"
                                                id="x_point"
                                                className="form-control"
                                                placeholder="x"
                                                value={slmOptions.focalSpot.x}
                                                onChange={(e) => { setSLMOptions(prev => ({ ...prev, focalSpot: { ...prev.focalSpot, x: e.target.value } })) }}
                                                style={{ margin: '0', borderRadius: '0' }}
                                            />
                                        </div>
                                        <div className="col-md-3" style={{ padding: '0' }}>
                                            <label for="y_point" style={{ display: 'block', textAlign: 'center' }}>Y</label>
                                            <input
                                                type="number"
                                                id="y_point"
                                                className="form-control"
                                                placeholder="y"
                                                value={slmOptions.focalSpot.y}
                                                onChange={(e) => { setSLMOptions(prev => ({ ...prev, focalSpot: { ...prev.focalSpot, y: e.target.value } })) }}
                                                style={{ margin: '0', borderRadius: '0' }}
                                            />
                                        </div>
                                        <div className="col-md-3" style={{ padding: '0' }}>
                                            <label for="z_point" style={{ display: 'block', textAlign: 'center' }}>Z</label>
                                            <input
                                                type="number"
                                                id="z_point"
                                                className="form-control"
                                                placeholder="z"
                                                value={slmOptions.focalSpot.z}
                                                onChange={(e) => { setSLMOptions(prev => ({ ...prev, focalSpot: { ...prev.focalSpot, z: e.target.value } })) }}
                                                style={{ margin: '0', borderRadius: '0' }}
                                            />
                                        </div>
                                        <div className="col-md-3" style={{ padding: '0' }}>
                                            <label for="intensity_point" style={{ display: 'block', textAlign: 'center' }}>Intensity</label>
                                            <input
                                                type="number"
                                                id="intensity_point"
                                                className="form-control"
                                                placeholder="i"
                                                value={slmOptions.focalSpot.intensity}
                                                onChange={(e) => { setSLMOptions(prev => ({ ...prev, focalSpot: { ...prev.focalSpot, intensity: e.target.value } })) }}

                                                style={{ margin: '0', borderRadius: '0' }}
                                            />
                                        </div>
                                    </div>
                                </Form>
                                <div className="row mt-3" style={{ marginBottom: '0' }}>
                                    <ButtonGroup aria-label="Button group">
                                        <Button
                                            key="Add"
                                            onClick={() => addNewFocalSpot(slmOptions.focalSpot.x, slmOptions.focalSpot.y, slmOptions.focalSpot.z, slmOptions.focalSpot.intensity, 100)}
                                            style={{ marginRight: '5px' }}
                                            disabled={slmOptions.focalSpot.id}
                                        >
                                            Add
                                        </Button>
                                        <Button
                                            disabled={!slmOptions.focalSpot.id}
                                            key="Remove"
                                            onClick={() => removeById(slmOptions.focalSpot.id)}
                                            className="btn btn-primary"
                                            style={{ marginRight: '5px' }}
                                        >
                                            Remove
                                        </Button>

                                        <Button
                                            disabled={!slmOptions.focalSpot.id}
                                            key="Update"
                                            className="btn btn-primary"
                                            onClick={() => updatePoint(slmOptions.focalSpot.x, slmOptions.focalSpot.y, slmOptions.focalSpot.z, slmOptions.focalSpot.intensity, slmOptions.focalSpot.id)}
                                            style={{ marginRight: '5px' }}

                                        >
                                            Update
                                        </Button>


                                        <Button

                                            key="Clear"

                                            className="btn btn-success"
                                            onClick={() => {
                                                setSLMOptions(prev => ({ ...prev, focalSpot: { x: 0, y: 0, z: 0, intensity: 1, id: "" } }))
                                            }}
                                        >
                                            Clear
                                        </Button>


                                    </ButtonGroup>
                                    <button className="btn btn-danger" style={{ width: '100%', marginTop: '10px' }}
                                        onClick={() => {
                                            setSLMOptions(prev => ({ ...prev, focalSpot: { x: 0, y: 0, z: 0, intensity: 1, id: "" } }))
                                            setPoints({});
                                        }}
                                    >Remove All Points</button>
                                </div>

                            </div>
                        </div>
                        <h5>Affine Parameters:</h5>
                        <div className="container">
                            <div className="row">
                                <Form>
                                    <table className="table">
                                        <thead>
                                            <tr>
                                                <th></th>
                                                <th className="text-center">SX</th>
                                                <th className="text-center">SY</th>
                                                <th className="text-center">CX</th>
                                                <th className="text-center">CY</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {['0', '1', '2'].map((num) => (
                                                <tr key={num}>
                                                    <td className="text-center">{num}</td>
                                                    <td style={{ padding: '0' }}>
                                                        <input
                                                            type="number"
                                                            id={`SX${num}`}
                                                            className="form-control text-center"
                                                            placeholder={`SX${num}`}
                                                            value={slmOptions.affine[`SLM_X_${num}`]}
                                                            onChange={(e) => { setSLMOptions(prev => ({ ...prev, affine: { ...prev.affine, [`SLM_X_${num}`]: e.target.value } })) }}
                                                            style={{ margin: '0', borderRadius: '0' }}
                                                        />
                                                    </td>
                                                    <td style={{ padding: '0' }}>
                                                        <input
                                                            type="number"
                                                            id={`SY${num}`}
                                                            className="form-control text-center"
                                                            placeholder={`SY${num}`}
                                                            value={slmOptions.affine[`SLM_Y_${num}`]}
                                                            onChange={(e) => { setSLMOptions(prev => ({ ...prev, affine: { ...prev.affine, [`SLM_Y_${num}`]: e.target.value } })) }}
                                                            style={{ margin: '0', borderRadius: '0' }}
                                                        />
                                                    </td>
                                                    <td style={{ padding: '0' }}>
                                                        <input
                                                            type="number"
                                                            id={`CX${num}`}
                                                            className="form-control text-center"
                                                            placeholder={`CX${num}`}
                                                            value={slmOptions.affine[`CAM_X_${num}`]}
                                                            onChange={(e) => { setSLMOptions(prev => ({ ...prev, affine: { ...prev.affine, [`CAM_X_${num}`]: e.target.value } })) }}
                                                            style={{ margin: '0', borderRadius: '0' }}
                                                        />
                                                    </td>
                                                    <td style={{ padding: '0' }}>
                                                        <input
                                                            type="number"
                                                            id={`CY${num}`}
                                                            className="form-control text-center"
                                                            placeholder={`CY${num}`}
                                                            value={slmOptions.affine[`CAM_Y_${num}`]}
                                                            onChange={(e) => { setSLMOptions(prev => ({ ...prev, affine: { ...prev.affine, [`CAM_Y_${num}`]: e.target.value } })) }}
                                                            style={{ margin: '0', borderRadius: '0' }}
                                                        />
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </Form>
                                <button type="submit" className="btn btn-warning"
                                    onClick={updateAffine}
                                    style={{
                                        width: '100%', marginTop: '10px'



                                    }}>Update Affine</button>
                            </div>
                        </div>

                    </CardBody>
                </Card>
            </Collapse>
        </div>
    );
}

export default SLMOptions;
