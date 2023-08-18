# Interface features

The interface must be able to translate messages arriving at a the *directory* I/O to proper L1 controller requests on the other side. 
It must also be able to do the same and transmit the right requests arriving at the *L1 controller* I/O to the right directory on the other side. 

<ins>Types of messages:</ins>
- Directory
	- Input
		- responseFromMemory
		- **responseFromCache**
		- **requestFromCache**
	- Output
		- **forwardToCache**
		- **responseToCache**
		- requestToMemory
- Cache
	- Input
		- responseFromDirOrSibling
		- forwardFromDir
		- mandatoryQueue
	- Output
		- **requestToDir**
		- **responseToDirOrSibling**

When a message arrives, it is an **event**. This event causes a **transition**. This transition will move the FSM to a new state. The transition causes **actions** to be performed. 

In our case when a message arrives in **responseFromCache, requestFromCache, responseFromDirOrSibling, forwardFromDir** in either side of the interface, we need to translate it to the right output message on each side. 


