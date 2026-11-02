import { useContext } from 'react'
import { TableContext } from './MyTable'
import { SortableContainer } from 'react-sortable-hoc'

const SortableBody = SortableContainer(props => <tbody {...props} />)

const arrayMoveImmutable = (array, oldIndex, newIndex) => {
    const newArray = [...array]
    const [item] = newArray.splice(oldIndex, 1)
    newArray.splice(newIndex, 0, item)
    return newArray
}

export const DraggableContainer = props => {

    const { customSave, setDataSource, dataSourceRef } = useContext(TableContext)

    const onSortEnd = ({ oldIndex, newIndex }) => {
        if (oldIndex !== newIndex) {
            const currentData = dataSourceRef?.current || []
            const sortedDataSource = arrayMoveImmutable(currentData.slice(), oldIndex, newIndex)
            setDataSource(sortedDataSource)
            customSave?.({}, sortedDataSource)
        }
    }

    return <SortableBody useDragHandle disableAutoscroll helperClass='row-dragging' onSortEnd={onSortEnd} {...props} />
}