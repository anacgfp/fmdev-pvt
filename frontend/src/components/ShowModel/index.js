
import React from 'react';



function ShowModel(props) {

    return(
        <PerfectScrollbar style={{ width: '100%', overflowX: 'auto' }}>
        <ConfigContainer size='big' style={{ color: '#000' }}>

          <Header>
            <h1>Modelos Salvos</h1>
          </Header>


          {!data.length && !loading ?
            <StatusMsgContainer> Sem modelos salvos para serem exibidos. </StatusMsgContainer>
            : null}

          {loading ?
            <LoadingContainer>
              <ProgressSpinner style={{ width: '50px', height: '50px' }} strokeWidth="4" fill="#EEEEEE" animationDuration=".5s" />
            </LoadingContainer>
            : null}

          {data.length && !loading ?
            <Table>
              <thead>
                <tr>
                  <FirstHeaderColumn>Nome</FirstHeaderColumn>
                  <HeaderColumn>Descrição</HeaderColumn>
                  <HeaderColumn>Criado em</HeaderColumn>
                  <HeaderColumn>Acurácia de teste</HeaderColumn>
                  <HeaderColumn>Última predição em</HeaderColumn>
                  <HeaderColumn>Predições realizadas</HeaderColumn>
                  <HeaderColumn><div style={{ display: 'flex', justifyContent: 'center' }}>Ações</div></HeaderColumn>
                </tr>
              </thead>

              <tbody>
                {data.map((item, idx) => this.renderItem(item, idx))}
              </tbody>
            </Table>
            : null}

          {this.renderMenuActions()}
          <AlertDialog onSubmit={this.deleteModel}></AlertDialog>
        </ConfigContainer >
      </PerfectScrollbar>

    );
}