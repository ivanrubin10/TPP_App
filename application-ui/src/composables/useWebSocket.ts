import { io, Socket } from 'socket.io-client';
import { onMounted, onUnmounted } from 'vue';
import { useAppStore } from '@/stores/useAppStore';
import type { CarItem } from '@/types';

interface QueuedCar {
  car_id: string;
  date: string;
  expected_part: string;
  is_processed: boolean;
}

interface ConnectionStatus {
  status: boolean;
}

interface ConnectionType {
  type: 'PLC' | 'GALC';
}

interface PLCMessage {
  message: string;
}

export function useWebSocket() {
  const socket: Socket = io('http://localhost:5000', {
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5
  });

  const store = useAppStore();

  const setupSocketListeners = () => {
    socket.on('connect', () => {
      console.log('Socket connected');
    });

    socket.on('disconnect', () => {
      console.log('Socket disconnected');
      store.setConnectionStatus(false);
    });

    socket.on('connection_status', (data: ConnectionStatus) => {
      store.setConnectionStatus(data.status);
    });

    socket.on('connection_type', (data: ConnectionType) => {
      store.setConnectionType(data.type);
    });

    socket.on('plc_message', async (data: PLCMessage) => {
      console.log('Received message from PLC:', data.message);
      // Handle PLC message based on your application logic
    });

    socket.on('new_queued_car', (queuedCar: QueuedCar) => {
      console.log('Received new queued car:', queuedCar);
      const newCar: CarItem = {
        id: queuedCar.car_id,
        expectedPart: queuedCar.expected_part,
        actualPart: '',
        outcome: '',
        image: '',
        resultImage: '',
        date: queuedCar.date,
        isQueued: true
      };
      store.addItem(newCar);
      console.log('Added queued car to store:', newCar);
    });

    socket.on('handle_message', async (data: { message: string }) => {
      console.log('Received message from GALC:', data.message);
      // Handle GALC message based on your application logic
    });
  };

  onMounted(() => {
    setupSocketListeners();
  });

  onUnmounted(() => {
    socket.off('connect');
    socket.off('disconnect');
    socket.off('connection_status');
    socket.off('connection_type');
    socket.off('plc_message');
    socket.off('new_queued_car');
    socket.off('handle_message');
    socket.close();
  });

  const emit = (event: string, data?: any) => {
    socket.emit(event, data);
  };

  return {
    socket,
    emit
  };
} 