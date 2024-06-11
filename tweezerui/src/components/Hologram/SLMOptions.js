import React, { useState, useEffect, useRef } from 'react';
import { Collapse, CardBody, Card, CardTitle, Input, } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronDown, faChevronUp } from '@fortawesome/free-solid-svg-icons';
import { Form, Button, Row, Container, Col, FormGroup, Modal } from 'react-bootstrap';
import { useGlobalContext } from '../../GlobalContext';
import axios from 'axios';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { Slide } from 'react-toastify';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import p5 from 'p5';

function SLMOptions() {


    const { serverInfo, slmOptions, setSLMOptions, canvasRefs } = useGlobalContext();
    const [activeButtonSpotAction, setActiveButtonSpotAction] = useState("Add");



    const toggle = () => {
        setSLMOptions(prev => ({ ...prev, isCollapsed: !prev.isCollapsed }));
    };

    const handleUpdateAffine = () => {
    }


    const [points, setPoints] = useState([]);
    const [selectedPoint, setSelectedPoint] = useState(null);
    const [dragging, setDragging] = useState(false);







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