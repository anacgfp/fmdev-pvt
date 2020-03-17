import api from '../../services/api';
import { Creators } from '../ducks/pre_processing';
import { call, put } from 'redux-saga/effects';
import { actions as toastrActions } from 'react-redux-toastr';


export function* getIndicatorMetadata({ filter }) {
  try {
    yield put(Creators.preProcessingRequest());
    const response = yield call(api.post, 'pre-processing', filter);

    yield put(Creators.preProcessingSuccess(response.data));
  } catch (err) {
    yield put(Creators.preProcessingError({ err }));
    yield put(toastrActions.add({
      type: 'error',
      title: 'Erro',
      message: 'Falha ao listar Indicadores'
    }));
  }
}