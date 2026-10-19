import { FoodListing, FoodListingStatus } from '../types';
import { mockRepository } from './mockRepository';
import { apiClient, isApiMode } from './apiClient';
import { adaptFoodListing } from './apiAdapters';

export const foodService = {
  /**
   * Fetches active food listings.
   */
  async getFoodListings(): Promise<FoodListing[]> {
    if (!isApiMode()) {
      return mockRepository.getFoodListings();
    }

    const res = await apiClient.get<{ count: number; results: any[] } | any[]>('/resources/');
    const rawList = Array.isArray(res.data) ? res.data : (res.data?.results || []);
    return rawList.map(adaptFoodListing);
  },

  /**
   * Retrieves single food listing by ID.
   */
  async getListingById(id: string): Promise<FoodListing | undefined> {
    if (!isApiMode()) {
      const listings = mockRepository.getFoodListings();
      return listings.find((l) => l.id === id);
    }

    try {
      const res = await apiClient.get(`/resources/${id}/`);
      return adaptFoodListing(res.data);
    } catch {
      return undefined;
    }
  },

  /**
   * Fetches listings registered by a specific provider organization.
   */
  async getListingsByProvider(providerId: string): Promise<FoodListing[]> {
    if (!isApiMode()) {
      const listings = mockRepository.getFoodListings();
      return listings.filter((l) => l.providerId === providerId);
    }

    const all = await this.getFoodListings();
    return all.filter((l) => l.providerId === providerId);
  },

  /**
   * Persists a new surplus food listing to PostgreSQL.
   */
  async createListing(
    listingData: Omit<FoodListing, 'id' | 'createdAt' | 'status'>
  ): Promise<FoodListing> {
    if (!isApiMode()) {
      const newListing: FoodListing = {
        ...listingData,
        id: `FOOD-${Date.now().toString().slice(-4)}`,
        status: 'available',
        createdAt: new Date().toISOString(),
      };
      mockRepository.addFoodListing(newListing);
      return newListing;
    }

    const payload = {
      name: listingData.name,
      category: String(listingData.category || 'cooked_meals').toLowerCase().replace(/[\s-]/g, '_'),
      quantity: Number(listingData.quantity),
      unit: listingData.unit || 'kg',
      pickupStart: listingData.pickupStart,
      pickupEnd: listingData.pickupEnd,
      safeUntil: listingData.safeUntil,
      storageRequirements: listingData.storageRequirements || 'Ambient',
      dietaryTags: listingData.dietaryTags || [],
      safetyNotes: listingData.safetyNotes || '',
    };

    const res = await apiClient.post('/resources/', payload);
    return adaptFoodListing(res.data);
  },

  /**
   * Withdraws a surplus listing from circulation.
   */
  async withdrawListing(id: string): Promise<void> {
    if (!isApiMode()) {
      mockRepository.updateFoodListing(id, { status: 'expired' });
      return;
    }

    await apiClient.post(`/resources/${id}/withdraw/`);
  },

  /**
   * Backward compatibility for updating listing status.
   */
  async updateListingStatus(id: string, status: FoodListingStatus): Promise<void> {
    if (!isApiMode()) {
      mockRepository.updateFoodListing(id, { status });
      return;
    }

    if (status === 'expired') {
      await this.withdrawListing(id);
    }
  },
};

export default foodService;
