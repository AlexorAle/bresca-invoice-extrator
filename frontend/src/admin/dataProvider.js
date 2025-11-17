/**
 * DataProvider personalizado para React-admin
 * Adapta las respuestas de FastAPI al formato esperado por React-admin
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/invoice-api/api';

/**
 * Wrapper para fetch con manejo de errores
 */
async function fetchAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      let errorDetail = `Error ${response.status}`;
      try {
        const error = await response.json();
        if (error.detail) {
          errorDetail = typeof error.detail === 'string' 
            ? error.detail 
            : JSON.stringify(error.detail);
        }
      } catch (e) {
        errorDetail = `Error ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorDetail);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error en API ${endpoint}:`, error);
    throw error;
  }
}

/**
 * DataProvider personalizado para FastAPI
 */
export const dataProvider = {
  getList: async (resource, params) => {
    const { page, perPage } = params.pagination;
    const { field, order } = params.sort || {};
    const filter = params.filter || {};

    try {
      let endpoint = '';
      let response = null;

      if (resource === 'facturas') {
        // Construir endpoint con filtros
        const month = filter.month || new Date().getMonth() + 1;
        const year = filter.year || new Date().getFullYear();
        endpoint = `/facturas/list?month=${month}&year=${year}`;
        
        response = await fetchAPI(endpoint);
        
        // Adaptar formato FastAPI a React-admin
        let data = response.data || response || [];
        
        // Aplicar filtros adicionales
        if (filter.proveedor) {
          data = data.filter(item => 
            item.proveedor?.toLowerCase().includes(filter.proveedor.toLowerCase())
          );
        }
        if (filter.estado) {
          data = data.filter(item => item.estado === filter.estado);
        }
        if (filter.fecha_gte) {
          data = data.filter(item => new Date(item.fecha) >= new Date(filter.fecha_gte));
        }
        if (filter.fecha_lte) {
          data = data.filter(item => new Date(item.fecha) <= new Date(filter.fecha_lte));
        }
        if (filter.total_gte) {
          data = data.filter(item => parseFloat(item.total || 0) >= parseFloat(filter.total_gte));
        }
        if (filter.total_lte) {
          data = data.filter(item => parseFloat(item.total || 0) <= parseFloat(filter.total_lte));
        }

        // Aplicar sorting
        if (field && order) {
          data.sort((a, b) => {
            const aVal = a[field] || '';
            const bVal = b[field] || '';
            const comparison = aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
            return order === 'ASC' ? comparison : -comparison;
          });
        }

        // Aplicar paginación
        const total = data.length;
        const start = (page - 1) * perPage;
        const end = start + perPage;
        data = data.slice(start, end);

        // Agregar ID si no existe
        data = data.map((item, index) => ({
          ...item,
          id: item.id || item.factura_id || `temp-${start + index}`,
        }));

        return {
          data,
          total,
          page,
          perPage,
        };
      }

      // Para recursos personalizados (pendientes, reportes, carga-datos)
      // que no usan el dataProvider, devolver estructura vacía
      if (resource === 'pendientes' || resource === 'reportes' || resource === 'carga-datos') {
        return {
          data: [],
          total: 0,
          page: 1,
          perPage: 25,
        };
      }

      // Para otros recursos, devolver estructura básica
      return {
        data: [],
        total: 0,
        page: 1,
        perPage: 25,
      };
    } catch (error) {
      console.error(`Error en getList para ${resource}:`, error);
      throw error;
    }
  },

  getOne: async (resource, params) => {
    try {
      if (resource === 'facturas') {
        // Buscar factura por ID en la lista
        const month = params.filter?.month || new Date().getMonth() + 1;
        const year = params.filter?.year || new Date().getFullYear();
        const endpoint = `/facturas/list?month=${month}&year=${year}`;
        
        const response = await fetchAPI(endpoint);
        const data = response.data || response || [];
        const item = data.find(f => 
          (f.id || f.factura_id) === params.id || 
          f.factura_id?.toString() === params.id?.toString()
        );

        if (!item) {
          throw new Error(`Factura con ID ${params.id} no encontrada`);
        }

        return {
          data: {
            ...item,
            id: item.id || item.factura_id || params.id,
          },
        };
      }

      throw new Error(`Resource ${resource} no soportado`);
    } catch (error) {
      console.error(`Error en getOne para ${resource}:`, error);
      throw error;
    }
  },

  getMany: async (resource, params) => {
    try {
      // Por ahora, usar getList y filtrar por IDs
      const result = await dataProvider.getList(resource, {
        pagination: { page: 1, perPage: 1000 },
        sort: {},
        filter: {},
      });

      const filtered = result.data.filter(item => 
        params.ids.includes(item.id)
      );

      return {
        data: filtered,
      };
    } catch (error) {
      console.error(`Error en getMany para ${resource}:`, error);
      throw error;
    }
  },

  getManyReference: async (resource, params) => {
    // Por ahora, devolver estructura básica
    return {
      data: [],
      total: 0,
    };
  },

  create: async (resource, params) => {
    // Por ahora, no soportado (backend no tiene endpoint de creación)
    throw new Error(`Create no implementado para ${resource}`);
  },

  update: async (resource, params) => {
    // Por ahora, no soportado (backend no tiene endpoint de actualización)
    throw new Error(`Update no implementado para ${resource}`);
  },

  updateMany: async (resource, params) => {
    // Por ahora, no soportado
    throw new Error(`UpdateMany no implementado para ${resource}`);
  },

  delete: async (resource, params) => {
    // Por ahora, no soportado (backend no tiene endpoint de eliminación)
    throw new Error(`Delete no implementado para ${resource}`);
  },

  deleteMany: async (resource, params) => {
    // Por ahora, no soportado
    throw new Error(`DeleteMany no implementado para ${resource}`);
  },
};

