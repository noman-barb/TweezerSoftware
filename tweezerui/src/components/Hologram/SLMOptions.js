import React, { useState, useEffect, useRef } from 'react';
import { Collapse, CardBody, Card } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronDown, faChevronUp } from '@fortawesome/free-solid-svg-icons';
import { Form, Button, ButtonGroup } from 'react-bootstrap';
import { useGlobalContext } from '../../GlobalContext';


function SLMOptions() {
    const { serverInfo, slmOptions, setSLMOptions, canvasRefs } = useGlobalContext();
    const [activeButtonSpotAction, setActiveButtonSpotAction] = useState("Add");

    const toggle = () => {
        setSLMOptions(prev => ({ ...prev, isCollapsed: !prev.isCollapsed }));
    };

    const mousePosition = useRef({ x: 0, y: 0 });
    const [points, setPoints] = useState({});
    const selectedPoint = useRef(null);
    const [isDragging, setIsDragging] = useState(false);



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

    useEffect(() => {
        const canvas = canvasRefs[4].current;
        

        const addPoint = () => {
            const { x, y } = mousePosition.current;

            const key = `${x}_${y}`;
           

            const newPoint = [x, y, slmOptions.currentZ, slmOptions.currentIntensity];
           
            setPoints(prev => ({ ...prev, [key]: newPoint }));
        };


        const removePoint = () => {
            const { x, y } = mousePosition.current;
           

            const { nearestPointKey, minDistance } = findNearestPoint(points, x, y);

            if (minDistance > 100) {
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


        const handleMouseMove = (event) => {
            const rect = canvas.getBoundingClientRect();
            const mouseX = event.clientX - rect.left;
            const mouseY = event.clientY - rect.top;

            mousePosition.current = { x: mouseX, y: mouseY };

            if (selectedPoint.current) {
                const { x, y } = mousePosition.current;
                const point = points[selectedPoint.current];
                point[0] = x;
                point[1] = y;
                setPoints(prev => ({ ...prev, [selectedPoint.current]: point }));
                console.log(points);
            }
        };

        const handleKeyPress = (event) => {
            switch (event.key.toUpperCase()) {
                case 'A':
                    addPoint();
                    break;
                case 'R':
                    removePoint();
                    break;
                case 'E':
                    break;
                default:
                    break;
            }
        };

        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('keypress', handleKeyPress);
        // event listener for mousedown and mouseup
        window.addEventListener('mousedown', (event) => { setIsDragging(true);});
        window.addEventListener('mouseup', (event) => { setIsDragging(false); });

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('keypress', handleKeyPress);
        };
    }, [points, canvasRefs, slmOptions]);



    // use effect for isDragging
    useEffect(() => {
        
        if (isDragging) {
            const { x, y } = mousePosition.current;
            const { nearestPointKey, minDistance } = findNearestPoint(points, x, y);

            if (minDistance < 100) {
                selectedPoint.current = nearestPointKey;
            }
        } else {
            selectedPoint.current = null;
        }
    }, [isDragging]);


   



    useEffect(() => {

        const canvas = canvasRefs[4].current;
        const context = canvas.getContext('2d');
        context.clearRect(0, 0, canvas.width, canvas.height);
        for (const key in points) {
            const point = points[key];
            context.beginPath();
            context.arc(point[0], point[1], 5, 0, 2 * Math.PI);
            context.fillStyle = 'red';
            context.fill();
        }

        // for selected point, have a white circle around it
        if (selectedPoint.current) {
            const point = points[selectedPoint.current];
            context.beginPath();
            context.arc(point[0], point[1], 10, 0, 2 * Math.PI);
            context.strokeStyle = 'white';
            context.stroke();
        }
    }, [points, canvasRefs[4], isDragging]);





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
                </div>

                <div className='fs-5 fw-bold' style={{ marginLeft: 'auto', padding: '10px', color: "black" }}>
                    <FontAwesomeIcon icon={slmOptions.isCollapsed ? faChevronUp : faChevronDown} />
                </div>
            </div>

            <Collapse isOpen={slmOptions.isCollapsed}>
                <Card className="rounded-bottom">
                    <CardBody>
                        <h5>Focal Spots:</h5>
                        <div className='container'>
                            <div className="row">
                                <Form className="container">
                                    <div className="row form-group" style={{ marginBottom: '0' }}>
                                        <div className="col-md-3" style={{ padding: '0' }}>
                                            <input
                                                type="number"
                                                id={`x_point`}
                                                className="form-control"
                                                placeholder={`x`}
                                                style={{ margin: '0', borderRadius: '0' }}
                                            />
                                        </div>
                                        <div className="col-md-3" style={{ padding: '0' }}>
                                            <input
                                                type="number"
                                                id={`y_point`}
                                                className="form-control"
                                                placeholder={`y`}
                                                style={{ margin: '0', borderRadius: '0' }}
                                            />
                                        </div>
                                        <div className="col-md-3" style={{ padding: '0' }}>
                                            <input
                                                type="number"
                                                id={`z_point`}
                                                className="form-control"
                                                placeholder={`z`}
                                                style={{ margin: '0', borderRadius: '0' }}
                                            />
                                        </div>
                                        <div className="col-md-3" style={{ padding: '0' }}>
                                            <input
                                                type="number"
                                                id={`intensity_point`}
                                                className="form-control"
                                                placeholder={`i`}
                                                style={{ margin: '0', borderRadius: '0' }}
                                            />
                                        </div>
                                    </div>
                                </Form>
                                <div className="row mt-3" style={{ marginBottom: '0' }}>
                                    <ButtonGroup aria-label="Button group">
                                        {['Add', 'Remove', 'Drag'].map((action) => {
                                            return (
                                                <Button
                                                    key={action}
                                                    onClick={() => setActiveButtonSpotAction(action)}
                                                    variant={activeButtonSpotAction === action ? 'primary' : 'secondary'}
                                                >
                                                    {action}
                                                </Button>
                                            );
                                        })}
                                    </ButtonGroup>
                                </div>
                                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '10px' }}>Process</button>
                            </div>
                        </div>
                        <h5>Affine Parameters:</h5>
                        <div className="container">
                            <div className="row">
                                <Form>
                                    {['0', '1', '2'].map((num) => (
                                        <div className="row form-group" key={num} style={{ marginBottom: '0' }}>
                                            <div className="col-md-3" style={{ padding: '0' }}>
                                                <input
                                                    type="number"
                                                    id={`SX${num}`}
                                                    className="form-control"
                                                    placeholder={`SX${num}`}
                                                    style={{ margin: '0', borderRadius: '0' }}
                                                />
                                            </div>
                                            <div className="col-md-3" style={{ padding: '0' }}>
                                                <input
                                                    type="number"
                                                    id={`SY${num}`}
                                                    className="form-control"
                                                    placeholder={`SY${num}`}
                                                    style={{ margin: '0', borderRadius: '0' }}
                                                />
                                            </div>
                                            <div className="col-md-3" style={{ padding: '0' }}>
                                                <input
                                                    type="number"
                                                    id={`CX${num}`}
                                                    className="form-control"
                                                    placeholder={`CX${num}`}
                                                    style={{ margin: '0', borderRadius: '0' }}
                                                />
                                            </div>
                                            <div className="col-md-3" style={{ padding: '0' }}>
                                                <input
                                                    type="number"
                                                    id={`CY${num}`}
                                                    className="form-control"
                                                    placeholder={`CY${num}`}
                                                    style={{ margin: '0', borderRadius: '0' }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </Form>
                                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '10px' }}>Update Affine</button>
                            </div>
                        </div>
                    </CardBody>
                </Card>
            </Collapse>
        </div>
    );
}

export default SLMOptions;
