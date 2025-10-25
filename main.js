// main.js

// TODO: Replace with your app's actual Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCWyx-mFqHWF9bj4UCMWuBD0A6BOhP-Oq8",
  authDomain: "meet-ebd8a.firebaseapp.com",
  projectId: "meet-ebd8a",
  storageBucket: "meet-ebd8a.firebasestorage.app",
  messagingSenderId: "642169862175",
  appId: "1:642169862175:web:b2a6f6b26a1579486a3d2a",
  measurementId: "G-RQBN1YYX6E"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Get references
const db = firebase.database();
const messageRef = db.ref('liveData/message');
const liveDataElement = document.getElementById('live-data');

// LISTEN FOR LIVE CHANGES
messageRef.on('value', (snapshot) => {
    const data = snapshot.val();
    liveDataElement.innerText = data || 'No live message set.';
});

// Function to write data
function updateMessage() {
    const newMessage = document.getElementById('new-message').value;
    if (newMessage) {
        messageRef.set(newMessage)
            .then(() => {
                document.getElementById('new-message').value = '';
            })
            .catch((error) => {
                console.error("Data could not be saved: " + error);
            });
    }
}