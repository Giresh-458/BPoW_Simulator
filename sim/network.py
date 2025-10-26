"""
Network simulation for blockchain communication with latency.
"""

import threading
import time
import queue
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass

@dataclass
class NetworkMessage:
    """Represents a message sent through the network."""
    sender: str
    recipient: str
    message_type: str
    data: Any
    timestamp: float
    delay: float

class Network:
    """Simulates network communication with configurable latency."""
    
    def __init__(self):
        """Initialize the network simulation."""
        self.message_queue = queue.PriorityQueue()
        self.subscribers: Dict[str, Callable] = {}
        self.running = False
        self.network_thread: Optional[threading.Thread] = None
        
    def start(self) -> None:
        """Start the network simulation thread."""
        if self.running:
            return
            
        self.running = True
        self.network_thread = threading.Thread(target=self._delivery_loop, daemon=True)
        self.network_thread.start()
        
    def stop(self) -> None:
        """Stop the network simulation."""
        self.running = False
        if self.network_thread:
            self.network_thread.join(timeout=1.0)
            
    def enqueue(self, message: NetworkMessage, delay_s: float = 0.1) -> None:
        """
        Add a message to the delivery queue.
        
        Args:
            message: The message to send
            delay_s: Delay in seconds before delivery
        """
        delivery_time = time.time() + delay_s
        self.message_queue.put((delivery_time, message))
        
    def subscribe(self, node_id: str, callback: Callable) -> None:
        """
        Subscribe a node to receive messages.
        
        Args:
            node_id: Unique identifier for the node
            callback: Function to call when message is received
        """
        self.subscribers[node_id] = callback
        
    def unsubscribe(self, node_id: str) -> None:
        """Unsubscribe a node from receiving messages."""
        if node_id in self.subscribers:
            del self.subscribers[node_id]
            
    def _delivery_loop(self) -> None:
        """Main network delivery loop that runs in a separate thread."""
        while self.running:
            try:
                # Get next message to deliver
                delivery_time, message = self.message_queue.get(timeout=0.1)
                
                # Wait until delivery time
                current_time = time.time()
                if delivery_time > current_time:
                    time.sleep(delivery_time - current_time)
                    
                # Deliver message to recipient
                if message.recipient in self.subscribers:
                    try:
                        self.subscribers[message.recipient](message)
                    except Exception as e:
                        print(f"Error delivering message to {message.recipient}: {e}")
                        
            except queue.Empty:
                # No messages to deliver, continue loop
                continue
            except Exception as e:
                print(f"Error in network delivery loop: {e}")
                
    def broadcast(self, sender: str, message_type: str, data: Any, 
                  delay_s: float = 0.1) -> None:
        """
        Broadcast a message to all subscribers.
        
        Args:
            sender: ID of the sender
            message_type: Type of message
            data: Message data
            delay_s: Delay before delivery
        """
        for recipient in self.subscribers.keys():
            message = NetworkMessage(
                sender=sender,
                recipient=recipient,
                message_type=message_type,
                data=data,
                timestamp=time.time(),
                delay=delay_s
            )
            self.enqueue(message, delay_s)
            
    def send_message(self, sender: str, recipient: str, message_type: str, 
                     data: Any, delay_s: float = 0.1) -> None:
        """
        Send a message to a specific recipient.
        
        Args:
            sender: ID of the sender
            recipient: ID of the recipient
            message_type: Type of message
            data: Message data
            delay_s: Delay before delivery
        """
        message = NetworkMessage(
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            data=data,
            timestamp=time.time(),
            delay=delay_s
        )
        self.enqueue(message, delay_s)
