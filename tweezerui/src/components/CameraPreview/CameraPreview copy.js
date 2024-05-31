import React, { useState, useEffect, useRef } from 'react';
import { Modal, Button, Form } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowDown, faCog } from '@fortawesome/free-solid-svg-icons';
import 'bootstrap/dist/css/bootstrap.min.css';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { Slide } from 'react-toastify';
import axios from 'axios';




function CameraPreview() {


  // toast


  const mainServerURL = "http://10.0.63.153:4000/"
  const camServer1URL = "http://10.0.63.153:4001"
  const camServer2URL = "http://10.0.63.153:4002"

  
  // booleans
  const [isPreviewCam1, setIsPreviewCam1] = useState(false);
  const [isPreviewCam2, setIsPreviewCam2] = useState(false);

  const [cam1StringheaderModal, setCam1StringheaderModal] = useState("Cam Server 1 Configuration");
  const [cam2StringheaderModal, setCam2StringheaderModal] = useState("Cam Server 2 Configuration");

  const [isSwitchCam1Active, setIsSwitchCam1Active] = useState(true);
  const [isSwitchCam2Active, setIsSwitchCam2Active] = useState(true);

  const [isStreamingCam1, setIsStreamingCam1] = useState(false);
  const [isStreamingCam2, setIsStreamingCam2] = useState(false);

  // modals booleans
  const [showCam1ModalSettings, setshowCam1ModalSettings] = useState(false);
  const [showCam2ModalSettings, setshowCam2ModalSettings] = useState(false);

  const [allCameras, setAllCameras] = useState([]);

  // map usestate data structure
  const [cam1FormValues, setCam1FormValues] = useState({
    cam1Id: 'Select Option',
    cam1FolderPath: 'F:/',
    cam1TargetFPS: '10',
    cam1ImageFormat: '',
    cam1ExposureTime: "10.0",
    cam1Gain: "1.0",
  });

  const [cam2FormValues, setCam2FormValues] = useState({
    cam2Id: 'Select Option',
    cam2FolderPath: 'F:/',
    cam2TargetFPS: '10',
    cam2ImageFormat: '',
    cam2ExposureTime: "10.0",
    cam2Gain: "1.0",
  });

  const [camera1Comment, setCamera1Comment] = useState("Select the camera ID from the dropdown list");
  const [camera1IsVirtual, setCamera1IsVirtual] = useState(false);

  const [camera2Comment, setCamera2Comment] = useState("Select the camera ID from the dropdown list");
  const [camera2IsVirtual, setCamera2IsVirtual] = useState(false);


  useEffect(() => {


    const selectedCamera = allCameras.find((camera) => camera.camera_id === cam1FormValues.cam1Id);

    if (!selectedCamera) {
      return;
    }
    const isVirtual = !selectedCamera.details.is_real;
    let comment = selectedCamera.details.comment;
    setCamera1IsVirtual(isVirtual);
    comment = comment + " | " + (isVirtual ? "Virtual Camera" : "Real Camera");
    setCamera1Comment(comment);



  }, [cam1FormValues, allCameras]);

  useEffect(() => {

    const selectedCamera = allCameras.find((camera) => camera.camera_id === cam2FormValues.cam2Id);
    if (!selectedCamera) {
      return;
    }

    const isVirtual = !selectedCamera.details.is_real;
    let comment = selectedCamera.details.comment;
    setCamera2IsVirtual(isVirtual);
    comment = comment + " | " + (isVirtual ? "Virtual Camera" : "Real Camera");
    setCamera2Comment(comment);

  }, [cam2FormValues, allCameras]);


  const handleCam1InputChange = (event) => {
    setCam1FormValues({
      ...cam1FormValues,
      [event.target.name]: event.target.value,
    });
  };

  const handleCam2InputChange = (event) => {
    setCam2FormValues({
      ...cam2FormValues,
      [event.target.name]: event.target.value,
    });

  };

  // properties of streaming
  const [fps1, setFps1] = useState(0);
  const [rxSpeed1, setRxSpeed1] = useState(0);
  const [fps2, setFps2] = useState(0);
  const [rxSpeed2, setRxSpeed2] = useState(0);

  // canvas
  const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 });
  const canvasRef = useRef(null);



  // modals handlers
  const handleCloseCam1Modal = () => setshowCam1ModalSettings(false);
  const handleshowCam1ModalSettings = () => setshowCam1ModalSettings(true);

  // modals handlers
  const handleCloseCam2Modal = () => setshowCam2ModalSettings(false);
  const handleshowCam2ModalSettings = () => setshowCam2ModalSettings(true);




  useEffect(() => {

    if (showCam1ModalSettings || showCam2ModalSettings) {

      axios.get(camServer1URL + "/get_all_camera_details")
        .then((response) => {

          setAllCameras(response.data.data);

        })
        .catch((error) => {
          showToast("Error in fetching camera details", "error", 2000);
          showToast(error.message, "error", 2000);
        }
        )

    }
  }, [showCam1ModalSettings, showCam2ModalSettings]);

  const showToast = (msg, type, delay) => {

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




  const startPreviewCam1 = () => {



    setIsSwitchCam1Active(false);

    if (!isPreviewCam1) {

      let toastId = toast.loading("Warming up Cam 1 Server", {
        position: "top-center",
        autoClose: 2000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
        theme: "dark",
        transition: Slide,
      }
      );


      axios.get(mainServerURL + "warmup/camserver/1")
        .then((response) => {
          const success = response.data.success;
          const msg = response.data.msg;
          setIsSwitchCam1Active(true);

          if (success) {
            toast.update(toastId, {
              render: msg,
              type: "success",
              isLoading: false,
              autoClose: 2000,
            });

            setIsPreviewCam1(true);

          } else {
            toast.update(toastId, {
              render: msg,
              type: "error",
              isLoading: false,
              autoClose: 2000,
            });
          }
        })
        .catch((error) => {
          showToast("Error in warming up Cam Server 1", "error", 2000);
          showToast(error.message, "error", 2000);
        }
        )
    }
    else {



      let toastId = toast.loading("Shuting down Cam Server 1", {
        position: "top-center",
        autoClose: 2000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
        theme: "dark",
        transition: Slide,
      });


      // TODO
      axios.post(camServer1URL + "/stop_camera/")
        .then((response) => {
          const success = response.data.success;
          const msg = response.data.msg;
          setIsSwitchCam1Active(true);
          if (success) {
            toast.update(toastId, {
              render: msg,
              type: "success",
              isLoading: false,
              autoClose: 1000,
            });
            setIsStreamingCam1(false);
            setIsPreviewCam1(false);


          } else {
            toast.update(toastId, {
              render: msg,
              type: "error",
              isLoading: false,
              autoClose: 1000,
            });


          }
        })
        .catch((error) => {
          showToast("Error in shutting down Cam Server 1", "error", 2000);
          showToast(error.message, "error", 2000);
        }
        )

    }


  };

  const startPreviewCam2 = () => {
    setIsSwitchCam2Active(false);

    if (!isPreviewCam2) {
      let toastId = toast.loading("Warming up Cam 2 Server", {
        position: "top-center",
        autoClose: 2000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
        theme: "dark",
        transition: Slide,
      });

      axios.get(mainServerURL + "warmup/camserver/2")
        .then((response) => {
          const success = response.data.success;
          const msg = response.data.msg;
          setIsSwitchCam2Active(true);

          if (success) {
            toast.update(toastId, {
              render: msg,
              type: "success",
              isLoading: false,
              autoClose: 2000,
            });

            setIsPreviewCam2(true);

          } else {
            toast.update(toastId, {
              render: msg,
              type: "error",
              isLoading: false,
              autoClose: 2000,
            });
          }
        })
        .catch((error) => {
          showToast("Error in warming up Cam Server 2", "error", 2000);
          showToast(error.message, "error", 2000);
        }
        )
    }
    else {
      let toastId = toast.loading("Shutting down Cam Server 2", {
        position: "top-center",
        autoClose: 2000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
        theme: "dark",
        transition: Slide,
      });

      axios.post(camServer2URL + "/stop_camera/")
        .then((response) => {
          const success = response.data.success;
          const msg = response.data.msg;
          setIsSwitchCam2Active(true);
          if (success) {
            toast.update(toastId, {
              render: msg,
              type: "success",
              isLoading: false,
              autoClose: 1000,
            });
            setIsStreamingCam2(false);
            setIsPreviewCam2(false);
          } else {
            toast.update(toastId, {
              render: msg,
              type: "error",
              isLoading: false,
              autoClose: 1000,
            });
          }
        })
        .catch((error) => {
          showToast("Error in shutting down Cam Server 2", "error", 2000);
          showToast(error.message, "error", 2000);
        }
        )
    }
  };


  const streamCam1 = () => {

    setIsSwitchCam1Active(false);

    if (isStreamingCam1) {

      let toastId = toast.loading("Stopping " + cam1FormValues.cam1Id, {
        position: "top-center",
        autoClose: 2000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
        theme: "dark",
        transition: Slide,
      });


      // stop streaming
      axios.post(camServer1URL + "/stop_camera/")
        .then((response) => {
          setIsSwitchCam1Active(true);

          const success = response.data.success;
          const msg = response.data.msg;
          if (success) {
            toast.update(toastId, {
              render: msg,
              type: "success",
              isLoading: false,
              autoClose: 2000,
            });
            setIsStreamingCam1(false);
          } else {
            toast.update(toastId, {
              render: msg,
              type: "error",
              isLoading: false,
              autoClose: 2000,
            });
          }
        })
        .catch((error) => {
          showToast("Error in stopping camera 1", "error", 2000);
          showToast(error.message, "error", 2000);
        }
        )
    }
    else {
      // start streaming


      let toastId = toast.loading("Starting " + cam1FormValues.cam1Id, {
        position: "top-center",
        autoClose: 2000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
        theme: "dark",
        transition: Slide,
      });

      let data = {
        camera_id: cam1FormValues.cam1Id,
        fps: cam1FormValues.cam1TargetFPS,
        exposure_time: cam1FormValues.cam1ExposureTime,
        gain: cam1FormValues.cam1Gain,
        image_format: cam1FormValues.cam1ImageFormat,
      };



      axios.post(camServer1URL + "/start_camera/", data)
        .then((response) => {
          setIsSwitchCam1Active(true);

          const success = response.data.success;
          const msg = response.data.msg;
          if (success) {
            setIsStreamingCam1(true);
            toast.update(toastId, {
              render: msg,
              type: "success",
              isLoading: false,
              autoClose: 2000,
            });
          } else {
            setIsStreamingCam1(false);
            toast.update(toastId, {
              render: msg,
              type: "error",
              isLoading: false,
              autoClose: 2000,
            });

          }
        })
        .catch((error) => {
          showToast("Error in starting camera 1", "error", 2000);
          showToast(error.message, "error", 2000);
        }
        )


    }

  };

  const streamCam2 = () => {

    setIsSwitchCam2Active(false);

    if (isStreamingCam2) {

      let toastId = toast.loading("Stopping " + cam2FormValues.cam2Id, {
        position: "top-center",
        autoClose: 2000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
        theme: "dark",
        transition: Slide,
      });


      // stop streaming
      axios.post(camServer2URL + "/stop_camera/")
        .then((response) => {
          setIsSwitchCam2Active(true);

          const success = response.data.success;
          const msg = response.data.msg;
          if (success) {
            toast.update(toastId, {
              render: msg,
              type: "success",
              isLoading: false,
              autoClose: 2000,
            });
            setIsStreamingCam2(false);
          } else {
            toast.update(toastId, {
              render: msg,
              type: "error",
              isLoading: false,
              autoClose: 2000,
            });
          }
        })
        .catch((error) => {
          showToast("Error in stopping camera 2", "error", 2000);
          showToast(error.message, "error", 2000);
        }
        )
    }
    else {
      // start streaming


      let toastId = toast.loading("Starting " + cam2FormValues.cam2Id, {
        position: "top-center",
        autoClose: 2000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
        theme: "dark",
        transition: Slide,
      });

      let data = {
        camera_id: cam2FormValues.cam2Id,
        fps: cam2FormValues.cam2TargetFPS,
        exposure_time: cam2FormValues.cam2ExposureTime,
        gain: cam2FormValues.cam2Gain,
        image_format: cam2FormValues.cam2ImageFormat,
      };



      axios.post(camServer2URL + "/start_camera/", data)
        .then((response) => {
          setIsSwitchCam2Active(true);

          const success = response.data.success;
          const msg = response.data.msg;
          if (success) {
            setIsStreamingCam2(true);
            toast.update(toastId, {
              render: msg,
              type: "success",
              isLoading: false,
              autoClose: 2000,
            });
          } else {
            setIsStreamingCam2(false);
            toast.update(toastId, {
              render: msg,
              type: "error",
              isLoading: false,
              autoClose: 2000,
            });

          }
        })
        .catch((error) => {
          showToast("Error in starting camera 2", "error", 2000);
          showToast(error.message, "error", 2000);
        }
        )


    }

  };



  useEffect(() => {
    if (canvasRef.current) {
      setCanvasSize({
        width: canvasRef.current.offsetWidth,
        height: canvasRef.current.offsetHeight,
      });
    }
  }, []);



  useEffect(() => {

    if (!isPreviewCam1) {
      return;
    }

    let frameCount = 0;
    let dataCount = 0;
    let firstImageReceived = false;
    // strip out http:// or https:// from the URL to get ip
    const ip = camServer1URL.replace(/(^\w+:|^)\/\//, '');
    const websocket = new WebSocket("ws://" + ip + "/ws");
    websocket.binaryType = 'blob';  // Since the images can be in binary format

    const updateFpsAndSpeed = () => {
      setFps1(frameCount);
      setRxSpeed1(dataCount / 1024);  // Speed in KB/s
      frameCount = 0;
      dataCount = 0;
    };

    const intervalId = setInterval(updateFpsAndSpeed, 1000); // Update FPS and speed every second

    const img = new Image();
    img.onload = () => {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (!firstImageReceived) {
        canvas.width = img.width;
        canvas.height = img.height;
        firstImageReceived = true;
      }
      // Draw a scaled down version of the image
      ctx.drawImage(img, 0, 0, img.width, img.height, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(img.src);
    };

    websocket.onmessage = (event) => {

      const url = URL.createObjectURL(event.data);
      img.src = url;  // Just change the source of the Image object
      frameCount++;
      dataCount += event.data.size;  // Add the size of the received data
    };

    websocket.onopen = () => console.log('Connected to server');
    websocket.onerror = (error) => console.error('WebSocket error:', error);
    websocket.onclose = () => {
      console.log('Disconnected from server');
      clearInterval(intervalId);
    };

    return () => {
      websocket.close();
      clearInterval(intervalId);
    };

  }, [isPreviewCam1]);


  useEffect(() => {

    if (!isPreviewCam2) {
      return;
    }

    let frameCount = 0;
    let dataCount = 0;
    let firstImageReceived = false;
    // strip out http:// or https:// from the URL to get ip
    const ip = camServer2URL.replace(/(^\w+:|^)\/\//, '');
    const websocket = new WebSocket("ws://" + ip + "/ws");
    websocket.binaryType = 'blob';  // Since the images can be in binary format

    const updateFpsAndSpeed = () => {
      setFps1(frameCount);
      setRxSpeed1(dataCount / 1024);  // Speed in KB/s
      frameCount = 0;
      dataCount = 0;
    };

    const intervalId = setInterval(updateFpsAndSpeed, 1000); // Update FPS and speed every second

    const img = new Image();
    img.onload = () => {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (!firstImageReceived) {
        canvas.width = img.width;
        canvas.height = img.height;
        firstImageReceived = true;
      }
      // Draw a scaled down version of the image
      ctx.drawImage(img, 0, 0, img.width, img.height, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(img.src);
    };

    websocket.onmessage = (event) => {

      const url = URL.createObjectURL(event.data);
      img.src = url;  // Just change the source of the Image object
      frameCount++;
      dataCount += event.data.size;  // Add the size of the received data
    };

    websocket.onopen = () => console.log('Connected to server');
    websocket.onerror = (error) => console.error('WebSocket error:', error);
    websocket.onclose = () => {
      console.log('Disconnected from server');
      clearInterval(intervalId);
    };

    return () => {
      websocket.close();
      clearInterval(intervalId);
    };

  }, [isPreviewCam2]);


  return (
    <div className="p-3">

      <div className="d-flex flex-row justify-content-between">


        <div className="d-flex justify-content-center  justify-content-center align-items-center">
          <span className="me-3 fs-4 fw-bold " style={{ color: (!isSwitchCam1Active || !isSwitchCam2Active) ? 'gray' : 'inherit' }}>
            Cam 1
          </span>

          <div className="form-check form-switch fs-5">
            <input
              className="form-check-input"
              type="checkbox"
              role="switch"
              disabled={!isSwitchCam1Active || !isSwitchCam2Active}
              checked={isPreviewCam1}
              onChange={() => startPreviewCam1()}
            />
          </div>


          <div className="d-flex  justify-content-center" style={{ marginLeft: '30px' }}>

            <div className="d-flex justify-content-between ">     <div className="btn-group">
              <Button variant="primary" onClick={handleshowCam1ModalSettings} disabled={(!isPreviewCam1 || !isSwitchCam1Active) || isStreamingCam1}>
                <FontAwesomeIcon icon={faCog} />
              </Button>
              <Button
                variant="primary"
                onClick={streamCam1}
                disabled={!isPreviewCam1 || !isSwitchCam1Active}
                style={{ backgroundColor: isStreamingCam1 ? 'orange' : '' }}
              >
                {isStreamingCam1 ? 'Stop Stream' : 'Start Stream'}
              </Button>
            </div>
            </div>

          </div>

          {isStreamingCam1 && (
            <div className="d-flex  justify-content-center" style={{ marginLeft: '30px' }}>
              <div>FPS: {(fps1).toFixed(2)} | Rx Speed: {(rxSpeed1 / 1024).toFixed(2)} Mb/s</div>

            </div>
          )}

        </div>



        <div className="d-flex justify-content-center justify-content-center align-items-center ">
          <span className="me-3 fs-4 fw-bold " style={{ color: (!isSwitchCam1Active || !isSwitchCam2Active) ? 'gray' : 'inherit' }}>
            Cam 2
          </span>

          <div className="form-check form-switch fs-5">
            <input
              className="form-check-input"
              type="checkbox"
              role="switch"
              disabled={!isSwitchCam1Active || !isSwitchCam2Active}
              checked={isPreviewCam2}
              onChange={() => startPreviewCam2()}
            />
          </div>




          <div className="d-flex  justify-content-center" style={{ marginLeft: '30px' }}>

            <div className="d-flex justify-content-between ">     <div className="btn-group">
              <Button variant="primary" onClick={handleshowCam2ModalSettings} disabled={!isPreviewCam2 || !isSwitchCam2Active}>
                <FontAwesomeIcon icon={faCog} />
              </Button>
              <Button variant="primary" onClick={streamCam2} disabled={!isPreviewCam2 || !isSwitchCam2Active}>
                Stream Cam 2
              </Button>
            </div>
            </div>

          </div>



          {isStreamingCam2 && (
            <div className="d-flex  justify-content-center" style={{ marginLeft: '30px' }}>
              <div>FPS: {(fps2).toFixed(2)} | Rx Speed: {(rxSpeed2 / 1024).toFixed(2)} Mb/s</div>

            </div>
          )}

        </div>

      </div>



      <div style={{ width: '100%', height: '100%', marginTop: '20px' }}>
        <canvas ref={canvasRef} style={{ width: '100%', height: '100%', backgroundColor: 'black' }}></canvas>
      </div>

      <Modal show={showCam1ModalSettings} onHide={handleCloseCam1Modal}>
        <Modal.Header closeButton>
          <Modal.Title>{cam1StringheaderModal}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Camera ID</Form.Label>
              <Form.Select name="cam1Id" onChange={handleCam1InputChange} value={cam1FormValues.cam1Id}>
                <option value="">Select Option</option>
                {allCameras.map((camera, index) => (
                  <option key={index} value={camera.camera_id}>
                    {camera.camera_id}
                  </option>
                ))}
              </Form.Select>
              <Form.Text className="text-muted">
                {
                  camera1Comment
                }
              </Form.Text>
            </Form.Group>
            {camera1IsVirtual && (
              <Form.Group className="mb-3">
                <Form.Label>Folder Path</Form.Label>
                <Form.Control name="cam1FolderPath" placeholder="Enter folder path" onChange={handleCam1InputChange} value={cam1FormValues.cam1FolderPath} />
              </Form.Group>
            )}
            <Form.Group className="mb-3">
              <Form.Label>Target Streaming FPS</Form.Label>
              <Form.Control name="cam1TargetFPS" type="number" placeholder="Enter FPS" onChange={handleCam1InputChange} value={cam1FormValues.cam1TargetFPS} />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Exposure Time (ms)</Form.Label>
              <Form.Control
                name="cam1ExposureTime"
                type="number"
                step="0.01"
                placeholder="Enter exposure time in ms"
                onChange={handleCam1InputChange}
                value={cam1FormValues.cam1ExposureTime}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Gain</Form.Label>
              <Form.Control
                name="cam1Gain"
                type="number"
                step="0.01"
                placeholder="Enter gain"
                onChange={handleCam1InputChange}
                value={cam1FormValues.cam1Gain}
              />
            </Form.Group>


            <Form.Group className="mb-3">
              <Form.Label>Image Format</Form.Label>
              <Form.Select name="cam1ImageFormat" onChange={handleCam1InputChange} value={cam1FormValues.cam1ImageFormat}>
                <option value="compressed">Compressed</option>
                <option value="original">Original</option>
              </Form.Select>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
        </Modal.Footer>
      </Modal>



      <Modal show={showCam2ModalSettings} onHide={handleCloseCam2Modal}>
        <Modal.Header closeButton>
          <Modal.Title>{cam2StringheaderModal}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Camera ID</Form.Label>
              <Form.Select name="cam2Id" onChange={handleCam2InputChange} value={cam2FormValues.cam2Id}>
                <option value="">Select Option</option>
                {allCameras.map((camera, index) => (
                  <option key={index} value={camera.camera_id}>
                    {camera.camera_id}
                  </option>
                ))}
              </Form.Select>
              <Form.Text className="text-muted">
                {
                  camera1Comment
                }
              </Form.Text>
            </Form.Group>
            {camera1IsVirtual && (
              <Form.Group className="mb-3">
                <Form.Label>Folder Path</Form.Label>
                <Form.Control name="cam2FolderPath" placeholder="Enter folder path" onChange={handleCam2InputChange} value={cam2FormValues.cam2FolderPath} />
              </Form.Group>
            )}
            <Form.Group className="mb-3">
              <Form.Label>Target Streaming FPS</Form.Label>
              <Form.Control name="cam2TargetFPS" type="number" placeholder="Enter FPS" onChange={handleCam2InputChange} value={cam2FormValues.cam2TargetFPS} />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Exposure Time (ms)</Form.Label>
              <Form.Control
                name="cam2ExposureTime"
                type="number"
                step="0.01"
                placeholder="Enter exposure time in ms"
                onChange={handleCam2InputChange}
                value={cam2FormValues.cam2ExposureTime}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Gain</Form.Label>
              <Form.Control
                name="cam2Gain"
                type="number"
                step="0.01"
                placeholder="Enter gain"
                onChange={handleCam2InputChange}
                value={cam2FormValues.cam2Gain}
              />
            </Form.Group>


            <Form.Group className="mb-3">
              <Form.Label>Image Format</Form.Label>
              <Form.Select name="cam2ImageFormat" onChange={handleCam2InputChange} value={cam2FormValues.cam2ImageFormat}>
                <option value="compressed">Compressed</option>
                <option value="original">Original</option>
              </Form.Select>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
        </Modal.Footer>
      </Modal>

      <ToastContainer />
    </div>
  );
}

export default CameraPreview;