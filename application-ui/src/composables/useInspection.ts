import { ref } from 'vue';
import { useBackendApi } from './useBackendApi';
import { useAppStore } from '@/stores/useAppStore';
import type { CarItem } from '@/types';

export function useInspection() {
  const store = useAppStore();
  const { captureImage, updateItem, addLog, sendToICS } = useBackendApi();
  
  const isProcessing = ref(false);

  const handleInspection = async (item: CarItem) => {
    if (isProcessing.value) {
      return;
    }

    isProcessing.value = true;
    try {
      // Prepare car parameters for ICS if using GALC
      const carParams = store.connectionType === 'GALC' ? {
        car_id: item.id,
        expected_part: item.expectedPart,
        actual_part: item.actualPart
      } : undefined;
      
      const data = await captureImage(carParams);
      
      // Update item with captured data
      const updatedItem: CarItem = {
        ...item,
        image: data.image,
        resultImage: data.result_image,
        actualPart: determineActualPart(data.objects.length),
        date: formatCurrentDate(),
        isQueued: false
      };

      // Determine outcome
      updatedItem.outcome = updatedItem.actualPart === updatedItem.expectedPart ? 'GOOD' : 'NOGOOD';

      // If GALC and NOGOOD, send to ICS
      if (store.connectionType === 'GALC' && updatedItem.outcome === 'NOGOOD') {
        await sendToICS({
          car_id: updatedItem.id,
          expected_part: updatedItem.expectedPart,
          actual_part: updatedItem.actualPart,
          image: data.result_image
        });
      }

      // Update or add the item
      if (item.id) {
        await updateItem(updatedItem);
        store.updateItem(updatedItem);
      } else {
        const newItem = await addLog(updatedItem);
        store.addItem(newItem);
      }

      return updatedItem;
    } catch (error) {
      console.error('Error during inspection:', error);
      throw error;
    } finally {
      isProcessing.value = false;
    }
  };

  const determineActualPart = (objectCount: number): string => {
    if (objectCount === 0) return "Capo tipo 1";
    if (objectCount === 2) return "Capo tipo 2";
    if (objectCount === 3) return "Capo tipo 3";
    return "";
  };

  const formatCurrentDate = (): string => {
    const now = new Date();
    return `${String(now.getDate()).padStart(2, '0')}-${String(now.getMonth() + 1).padStart(2, '0')}-${now.getFullYear()} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
  };

  return {
    handleInspection,
    isProcessing
  };
} 