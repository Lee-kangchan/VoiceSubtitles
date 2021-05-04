let localVideo = document.getElementById("localVideo");
let remoteVideo = document.getElementById("remoteVideo");
let localStream;

navigator.mediaDevices
  .getUserMedia({
    video: true,
    audio: false,
  })
  .then(gotStream)
  .catch((error) => console.error(error));

function gotStream(stream) {
  console.log("Adding local stream");
  localStream = stream;
  localVideo.srcObject = stream;
  sendMessage("got user media");
  if (isInitiator) {
    maybeStart();
  }
}
function sendMessage(message){
    console.log('Client sending message: ',message);
    socket.emit('message',message);
  }
  function createPeerConnection() {
    try {
      pc = new RTCPeerConnection(null);
      pc.onicecandidate = handleIceCandidate;
      pc.onaddstream = handleRemoteStreamAdded;
      console.log("Created RTCPeerConnection");
    } catch (e) {
      alert("connot create RTCPeerConnection object");
      return;
    }
  }
  
  function handleIceCandidate(event) {
    console.log("iceCandidateEvent", event);
    if (event.candidate) {
      sendMessage({
        type: "candidate",
        label: event.candidate.sdpMLineIndex,
        id: event.candidate.sdpMid,
        candidate: event.candidate.candidate,
      });
    } else {
      console.log("end of candidates");
    }
  }
  
  function handleCreateOfferError(event) {
    console.log("createOffer() error: ", event);
  }
  
  function handleRemoteStreamAdded(event) {
    console.log("remote stream added");
    remoteStream = event.stream;
    remoteVideo.srcObject = remoteStream;
  }